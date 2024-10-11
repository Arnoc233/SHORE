

# ==============================================
# PART I. Data Backup.
# ==============================================
import shutil, time, os

backup_thread_started = False

lock_file = "file.lock"

def choose_files_for_backup(src):
    """Getting all CSV files that have more than one line."""
    files_to_backup = []
    files_not_backed_up = []  # List to store files not meeting the criteria
    for filename in os.listdir(src):
        if filename.endswith('.csv'):
            file_path = os.path.join(src, filename)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # Only add files with more than one line to the backup list
                if len(lines) > 1:
                    files_to_backup.append(filename)
                else:
                    files_not_backed_up.append(filename)  # Record files not backed up
    return files_to_backup, files_not_backed_up

def backup_boards_data():
    while True:
        try:
            src = './static/boards_data'
            dst = './static/boards_data_backup'
            # Check which files are suitable for backup
            files_to_backup, files_not_backed_up = choose_files_for_backup(src)
            
            # Create the backup folder if it does not exist
            if not os.path.exists(dst):
                os.makedirs(dst)
            else:
                # print(f"Backup folder already exists. Skipping creation.")
                pass

            if files_to_backup:
                # Copy each eligible file to the backup folder
                for filename in files_to_backup:
                    shutil.copy(os.path.join(src, filename), os.path.join(dst, filename))
                print(f"备份成功 for {len(files_to_backup)} file(s) at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"跳过备份 at {time.strftime('%Y-%m-%d %H:%M:%S')}: No files to backup.")
            
            # Print files that were not backed up
            if files_not_backed_up:
                print(f"Files not backed up ({len(files_not_backed_up)}): {', '.join(files_not_backed_up)}")

        except Exception as e:
            print(f"Backup error: {e}")
        
        time.sleep(30)  # Sleep for half a minute



# ==============================================
# PART II. __init__
# ==============================================
from flask import Flask
app = Flask(__name__)



# ==============================================
# PART III. routes for Page_Welcome.
# ==============================================
# III.1. Welcome page first load.
# |---------------------------------------------
from flask import send_from_directory, render_template
@app.route('/')
def welcome():
    boards = [f[:-4] for f in os.listdir('./static/boards_data/') if f.endswith('.csv')]
    return render_template('welcome_template.html', boards=boards)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/uploaded_images','favicon.jpeg')

@app.route('/templates/favicon.jpeg')
def favicon_temp():
    return send_from_directory('static/uploaded_images','favicon.jpeg')


# III.2. Rename a board.
# |---------------------------------------------
@app.route('/rename_board', methods=['POST'])
def rename_board():
    try:
        old_name = request.json['old_name']
        new_name = request.json['new_name']

        old_path = f'./static/boards_data/{old_name}.csv'
        new_path = f'./static/boards_data/{new_name}.csv'

        if os.path.exists(old_path):
            os.rename(old_path, new_path)
        else:
            return jsonify({'error': f"Board '{old_name}' does not exist."}), 404

        # Rename the image library folder if it exists
        old_image_path = f'./static/uploaded_images/{old_name}'
        new_image_path = f'./static/uploaded_images/{new_name}'

        if os.path.exists(old_image_path):
            os.rename(old_image_path, new_image_path)

        # Rename the backup file if it exists
        old_backup_path = f'./static/boards_data_backup/{old_name}.csv'
        new_backup_path = f'./static/boards_data_backup/{new_name}.csv'

        if os.path.exists(old_backup_path):
            os.rename(old_backup_path, new_backup_path)

        # Update references in other CSV files
        for filename in os.listdir('./static/boards_data'):
            if filename.endswith('.csv'):
                filepath = os.path.join('./static/boards_data', filename)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()

                updated_content = content.replace(old_name, new_name)

                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(updated_content)

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


# III.3. Add a board.
# |---------------------------------------------
@app.route('/add_board', methods=['POST'])
def add_board():
    try:
        board_name = request.json['board_name']
        # 创建一个新的 csv 文件
        with open(f'./static/boards_data/{board_name}.csv', mode='w', newline='', encoding='utf-8', errors='ignore') as file:
            writer = csv.writer(file)
            writer.writerow(['CardID', 'CardName', 'CardContent', 'CardTop', 'CardLeft', 'CardWidth', 'CardHeight', 'CardBorderColor'])  # Add header
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


# III.4. Delete a board.
# |---------------------------------------------
@app.route('/delete_board', methods=['POST'])
def delete_board():
    try:
        # 删除本体
        board_name = request.json['board_name']
        os.remove(f'./static/boards_data/{board_name}.csv')

        # 删除备份
        if os.path.exists(f'./static/boards_data_backup/{board_name}.csv'): 
            os.remove(f'./static/boards_data_backup/{board_name}.csv')
        else: 
            pass

        # 删除上传的图片库
        if os.path.exists(f'./static/uploaded_images/{board_name}'):
            # 强制删除图片库目录及其内容
            shutil.rmtree(f'./static/uploaded_images/{board_name}')

            # 只能删除空目录
            # os.rmdir(f'./static/uploaded_images/{board_name}')
        else:
            pass

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500



# ==============================================
# PART IV. routes for first loading Page_Board.
# ==============================================
import csv
@app.route('/<board_name>')
def board_selecting(board_name):
    cards_data = read_csv_data(board_name)
    return render_template('boards_template.html', board_name=board_name, cards=cards_data)

def read_csv_data(board_name):
    '''从CSV中获取数值，并传给board_selecting()的cards_data。'''
    cards = []
    with open(f'./static/boards_data/{board_name}.csv', mode='r', newline='', encoding='utf-8', errors='ignore') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 8:  # Ensure the width and height columns are included
                # print(len(row))
                card = {
                    'id': row[0],
                    'name': row[1],
                    'content': row[2].strip('"'),
                    'top': row[3],
                    'left': row[4],
                    'width': row[5],
                    'height': row[6],
                    'color': row[7],
                    'z_index': row[8] if len(row) > 8 and row[8] else 0,  # Default z_index
                }
                cards.append(card)
    return cards

# 刚开始加载网页时，<img>按照src获取图片默认用的是GET，虽然没有写出来。
# 所以这里要补一个。注意此处需要使用绝对路径，否则pyinstaller编译成EXE之后会找不到文件。
@app.route('/uploaded_images/<board_name>/<filename>.png', methods=['GET'])
def uploaded_file(board_name, filename):
    directory = os.path.abspath(os.path.join("static","uploaded_images", board_name))  # Get absolute path
    file_path = os.path.join(directory, f'{filename}.png')

    if not os.path.exists(file_path):
        print(file_path)
        return 'File not found', 404

    return send_from_directory(directory, f'{filename}.png', mimetype='image/png')

@app.route('/get_content/<int:card_id>', methods=['GET'])
def get_content(card_id):
    board_name = request.args.get('board_name')  # 从查询参数中获取 board_name

    # 根据 board_name 构建 csv_path
    csv_path = f'.static/boards_data/{board_name}.csv'

    card_content = ''  # 默认为空内容
    try:
        with open(csv_path, mode='r', newline='', encoding='utf-8', errors='ignore') as file:
            reader = csv.reader(file)
            next(reader)  # 跳过表头
            for row in reader:
                if row[0] == str(card_id):  # 比较 card_id
                    card_content = row[2]  # 获取卡片内容
                    break
    except FileNotFoundError:
        return {'card_content': ''}, 404  # 如果文件不存在，返回 404
    except Exception as e:
        return {'error': str(e)}, 500  # 其他错误，返回 500

    return {'card_content': card_content}, 200, {'Content-Type': 'application/json; charset=utf-8'}  
    # 返回卡片内容



# ==============================================
# PART V. routes for client change saving.
# ==============================================
# V.1.  update card content.
# |---------------------------------------------
from flask import request, jsonify
import logging
from filelock import FileLock

@app.route('/update_card', methods=['POST'])
def update_card():
    # return jsonify({'status': 'test'})
    data = request.get_json()  # Get request data
    board_name = data['board_name']
    card_id = data['card_id']
    print(data.get('height'))
    try:
        if data.get('content'):
            # print(data.get('content'))
            print(f"更新卡片内容 for card_id:  {card_id}。")
            update_csv_data(
                board_name,
                card_id,
                content=data.get('content'),  # Use .get() to avoid KeyError
                height=data.get('height'),
            )
            return jsonify({'status': 'success'}), 200, {'Content-Type': 'application/json; charset=utf-8'}
        
        elif data.get('z_index'):
            print(f"更新卡片Z轴为 {data.get('z_index')} for card_id:  {card_id}。")
            update_csv_data(
                board_name,
                card_id,
                z_index=data.get('z_index', 0),
            )
            return jsonify({'status': 'success'}), 200, {'Content-Type': 'application/json; charset=utf-8'}

        else:
            print(f"更新卡片样式 for card_id: {card_id}。")
            update_csv_data(
                board_name,
                card_id,
                left=data.get('left'),
                top=data.get('top'),
                name=data.get('name'),
                width=data.get('width'),
                height=data.get('height'),
                color=data.get('color')
            )
            return jsonify({'status': 'success'}), 201, {'Content-Type': 'application/json; charset=utf-8'}


    except Exception as e:
        logging.error(f"Error in update_card: {str(e)}")
        return jsonify({'error': str(e)}), 500, {'Content-Type': 'application/json; charset=utf-8'}

def update_csv_data(board_name, card_id, content=None, left=None, top=None, name=None, width=None, height=None, color=None, z_index=None):
    lock = FileLock(f'./static/boards_data/{board_name}.csv.lock')
    temp_file_path = f'./static/boards_data/{board_name}_temp.csv'
    original_file_path = f'./static/boards_data/{board_name}.csv'

    with lock:
        rows = []
        with open(original_file_path, mode='r', newline='', encoding='utf-8', errors='ignore') as file:
            reader = csv.reader(file)
            rows = list(reader)

        for row in rows[1:]:  # Skip header
            if str(row[0]) == str(card_id):
                if name is not None:
                    row[1] = name
                if content is not None:
                    row[2] = f'"{content}"'
                if top is not None:
                    row[3] = int(top.replace('px', ''))
                if left is not None:
                    row[4] = int(left.replace('px', ''))
                if width is not None:
                    row[5] = int(width.replace('px', ''))
                if height is not None:
                    height = str(height)  # 确保是字符串类型
                    if height.endswith('px'):
                        row[6] = height.replace('px', '')  # 去掉 px
                    else:
                        row[6] = height;
                if color is not None:
                    row[7] = color
                if z_index is not None:
                    if len(row) > 8:  # Check if z_index can be updated
                        row[8] = z_index
                    else:
                        # If row has less than 9 elements, you can append a default value or handle it accordingly
                        row.append(z_index)  # This adds z_index if row is too short
                break

        # 数据验证
        if not validate_data(rows):
            print("数据验证失败，写入操作已取消")
            return

        with open(temp_file_path, mode='w', newline='', encoding='utf-8', errors='ignore') as temp_file:
            writer = csv.writer(temp_file)
            writer.writerows(rows)

        os.replace(temp_file_path, original_file_path)
        print("更新成功！")

# 特别修改过的数据验证。试图保证文件不会爆炸， ==============
def validate_data(rows):
    """验证数据的完整性和有效性"""
    for row in rows[1:]:  # Skip header
        if len(row) < 8:  # 检查列数
            return False
        try:
            # 检查数值类型
            int(row[3])  # CardTop
            int(row[4])  # CardLeft
            int(row[5])  # CardWidth
            int(row[6])  # CardHeight
        except ValueError:
            return False
    return True


# V.2.  add a card.
# |---------------------------------------------
@app.route('/add_card', methods=['POST'])
def add_card():
    try:
        data = request.get_json()
        board_name = data['board_name']
        card_id = data['card_id']
        content = data['content']
        card_name = data.get('card_name', '新卡片')
        top = data.get('top', 100)  # Default value if not provided
        left = data.get('left', 100)  # Default value if not provided
        width = data.get('width', 200)  # Default value if not provided
        height = data.get('height', 100)  # Default value if not provided
        borderTopColor = data.get('color', "transparent") # Default value if not provided
        z_index = data.get('z_index', 0)

        # Add card to CSV
        add_card_to_csv(board_name, card_id, card_name, content, top, left, width, height, borderTopColor, z_index)
        return jsonify({'status': 'success'}), 200, {'Content-Type': 'application/json; charset=utf-8'}
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500, {'Content-Type': 'application/json; charset=utf-8'}

def add_card_to_csv(board_name, card_id, card_name, content, top, left, width, height, borderTopColor, z_index=0):
    lock = FileLock(f'./static/boards_data/{board_name}.csv.lock')
    with lock:
        cards = []
        with open(f'./static/boards_data/{board_name}.csv', mode='r', newline='', encoding='utf-8', errors='ignore') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                cards.append(row)

        # Append the new card with its properties, including z_index
        cards.append([card_id, card_name, content, top, left, width, height, borderTopColor, z_index])  # 假设 z_index 列在第9个位置

        with open(f'./static/boards_data/{board_name}.csv', mode='w', newline='', encoding='utf-8', errors='ignore') as file:
            writer = csv.writer(file)
            writer.writerow(['CardID', 'CardName', 'CardContent', 'CardTop', 'CardLeft', 'CardWidth', 'CardHeight', 'CardBorderColor', 'z_index'])  # Header
            writer.writerows(cards)


# V.3.  delete a card.
# |---------------------------------------------
@app.route('/delete_card', methods=['POST'])
def delete_card():
    try:
        data = request.get_json()
        card_id = data['card_id']
        board_name = data['board_name']
        delete_card_from_csv(board_name, card_id)  # 自定义函数来处理 CSV 中的删除
        # print(board_name, card_id)
        return jsonify({'status': 'success'}), 200, {'Content-Type': 'application/json; charset=utf-8'}
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500, {'Content-Type': 'application/json; charset=utf-8'}

def delete_card_from_csv(board_name, card_id):
    lock = FileLock(f'./static/boards_data/{board_name}.csv.lock')
    with lock:
        rows = []
        with open(f'./static/boards_data/{board_name}.csv', mode='r', newline='', encoding='utf-8', errors='ignore') as file:
            reader = csv.reader(file)
            rows = [row for row in reader if str(row[0]) != str(card_id)]

        with open(f'./static/boards_data/{board_name}.csv', mode='w', newline='', encoding='utf-8', errors='ignore') as file:
            writer = csv.writer(file)
            writer.writerows(rows)


# V.4.  update card style.
# |---------------------------------------------
@app.route('/move_all_cards', methods=['POST'])
def move_all_cards():
    try:
        data = request.get_json()
        board_name = data['board_name']
        top_change = data['top_change']
        left_change = data['left_change']
        # 更新所有卡片位置
        update_all_cards_position(board_name, top_change, left_change)
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

def update_all_cards_position(board_name, top_change, left_change):
    cards = []
    with open(f'./static/boards_data/{board_name}.csv', mode='r', newline='', encoding='utf-8', errors='ignore') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            cards.append(row)
    
    for row in cards:
        row[3] = str(int(row[3]) + int(top_change))  # 更新 top
        row[4] = str(int(row[4]) + int(left_change))  # 更新 left
    
    with open(f'./static/boards_data/{board_name}.csv', mode='w', newline='', encoding='utf-8', errors='ignore') as file:
        writer = csv.writer(file)
        writer.writerow(['CardID', 'CardName', 'CardContent', 'CardTop', 'CardLeft', 'CardWidth', 'CardHeight', 'CardBorderColor'])  # Add header
        writer.writerows(cards)


# V.5.  upload images.
# |---------------------------------------------
@app.route('/uploads/<board_name>/<timestamp>', methods=['POST'])
def save_image(board_name, timestamp):

    create_board_directory(board_name)
    
    if 'image' not in request.files:
        return '没有上传图片', 400
    
    image = request.files['image']
    save_path = os.path.join("static","uploaded_images", board_name, f"{timestamp}.png")
    
    try:
        image.save(save_path)
        print("保存图片成功_savePath")
    except Exception as e:
        print("保存图片失败")
        return str(e), 500
    
    return '图片保存成功', 200

def create_board_directory(board_name):
    path = os.path.join("static","uploaded_images", board_name)
    if not os.path.exists(path):
        os.makedirs(path)


# V.6.  delete images.
# |---------------------------------------------
from urllib.parse import unquote

@app.route('/delete_image', methods=['POST'])
def delete_image():
    try:
        data = request.get_json()
        imageSrc = unquote(data['imageSrc'])
        print("deleting the image:")
        print('/static/'+imageSrc[22:])
        image_path = os.path.join("static",imageSrc[22:])
        if os.path.exists(image_path):
            os.remove(image_path)
            return jsonify({'status': 'success'}), 200, {'Content-Type': 'application/json; charset=utf-8'}
        else:
            return jsonify(error="Image not found"), 404, {'Content-Type': 'application/json; charset=utf-8'}
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500, {'Content-Type': 'application/json; charset=utf-8'}



# ==============================================
# PART END. Main Function
# ==============================================
import webbrowser, logging, threading

if __name__ == '__main__':

    print(f"当前服务器工作路径: {os.getcwd()}")

    # 每1分钟进行数据备份 (无奈之举)
    # Start the backup thread
    backup_thread = threading.Thread(target=backup_boards_data, daemon=True)
    backup_thread.start()

    # 设置日志级别为 ERROR，只显示错误信息
    # log = logging.getLogger('werkzeug')
    # log.setLevel(logging.ERROR)

    # 打开浏览器访问指定网址（如果先启动Flask，就会卡在Flask的界面）
    webbrowser.open('http://127.0.0.1:5000')


    # 启动 Flask 应用
    # app.run()
    app.run(debug=True)
