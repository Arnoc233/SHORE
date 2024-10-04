from flask import Flask, render_template, request, jsonify
from flask import send_from_directory
from filelock import FileLock

import csv

import webbrowser
import os
import logging

from urllib.parse import unquote

# 偶尔会出现数据完全丢失... 或者是文件损坏。
# 那我只能进行一点备份了...
import shutil
import threading
import time

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
            src = './boards_data'
            dst = './boards_data_backup'
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
        
        # time.sleep(60)  # Sleep for 1 minute
        time.sleep(30)  # Sleep for half a minute



app = Flask(__name__)
@app.route('/')
def welcome():
    boards = [f[:-4] for f in os.listdir('./boards_data/') if f.endswith('.csv')]
    return render_template('welcome_template.html', boards=boards)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('templates','favicon.jpeg')

@app.route('/templates/favicon.jpeg')
def favicon_temp():
    return send_from_directory('templates','favicon.jpeg')


@app.route('/<board_name>')
def board_selecting(board_name):
    cards_data = read_csv_data(board_name)
    return render_template('boards_template.html', board_name=board_name, cards=cards_data)

@app.route('/update_card', methods=['POST'])
def update_card():
    # return jsonify({'status': 'test'})
    data = request.get_json()  # Get request data
    board_name = data['board_name']
    card_id = data['card_id']
    try:
        if data.get('content'):
            print(f"更新卡片内容 for card_id:  {card_id}。")
            update_csv_data(
                board_name,
                card_id,
                content=data.get('content'),  # Use .get() to avoid KeyError
                height=data.get('height'),
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

def read_csv_data(board_name):
    cards = []
    with open(f'./boards_data/{board_name}.csv', mode='r', newline='', encoding='utf-8', errors='ignore') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 8:  # Ensure the width and height columns are included
                card = {
                    'id': row[0],
                    'name': row[1],
                    'content': row[2].strip('"'),
                    'top': row[3],
                    'left': row[4],
                    'width': row[5],
                    'height': row[6],
                    'color': row[7],
                }
                cards.append(card)
    return cards

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

def update_csv_data(board_name, card_id, content=None, left=None, top=None, name=None, width=None, height=None, color=None):
    lock = FileLock(f'./boards_data/{board_name}.csv.lock')
    temp_file_path = f'./boards_data/{board_name}_temp.csv'
    original_file_path = f'./boards_data/{board_name}.csv'

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
                    row[6] = int(height.replace('px', ''))
                if color is not None:
                    row[7] = color
                break

        # 数据验证
        if not validate_data(rows):
            print("数据验证失败，写入操作已取消")
            return

        # 将更新后的行写入临时文件
        with open(temp_file_path, mode='w', newline='', encoding='utf-8', errors='ignore') as temp_file:
            writer = csv.writer(temp_file)
            writer.writerows(rows)

        # 替换原文件
        os.replace(temp_file_path, original_file_path)
        print("更新成功！")


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
    lock = FileLock(f'./boards_data/{board_name}.csv.lock')
    with lock:
        rows = []
        with open(f'./boards_data/{board_name}.csv', mode='r', newline='', encoding='utf-8', errors='ignore') as file:
            reader = csv.reader(file)
            rows = [row for row in reader if str(row[0]) != str(card_id)]

        with open(f'./boards_data/{board_name}.csv', mode='w', newline='', encoding='utf-8', errors='ignore') as file:
            writer = csv.writer(file)
            writer.writerows(rows)


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

        # Add card to CSV
        add_card_to_csv(board_name, card_id, card_name, content, top, left, width, height, borderTopColor)
        return jsonify({'status': 'success'}), 200, {'Content-Type': 'application/json; charset=utf-8'}
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500, {'Content-Type': 'application/json; charset=utf-8'}

def add_card_to_csv(board_name, card_id, card_name, content, top, left, width, height, borderTopColor):
    lock = FileLock(f'./boards_data/{board_name}.csv.lock')
    with lock:
        cards = []
        # Read existing cards
        with open(f'./boards_data/{board_name}.csv', mode='r', newline='', encoding='utf-8', errors='ignore') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                cards.append(row)

        # Append the new card with its properties
        cards.append([card_id, card_name, content, top, left, width, height, borderTopColor])

        # Write updated card list back to CSV
        with open(f'./boards_data/{board_name}.csv', mode='w', newline='', encoding='utf-8', errors='ignore') as file:
            writer = csv.writer(file)
            writer.writerow(['CardID', 'CardName', 'CardContent', 'CardTop', 'CardLeft', 'CardWidth', 'CardHeight', 'CardBorderColor'])  # Header
            writer.writerows(cards)


@app.route('/add_board', methods=['POST'])
def add_board():
    try:
        board_name = request.json['board_name']
        # 创建一个新的 csv 文件
        with open(f'./boards_data/{board_name}.csv', mode='w', newline='', encoding='utf-8', errors='ignore') as file:
            writer = csv.writer(file)
            writer.writerow(['CardID', 'CardName', 'CardContent', 'CardTop', 'CardLeft', 'CardWidth', 'CardHeight', 'CardBorderColor'])  # Add header
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/rename_board', methods=['POST'])
def rename_board():
    try:
        old_name = request.json['old_name']
        new_name = request.json['new_name']

        old_path = f'./boards_data/{old_name}.csv'
        new_path = f'./boards_data/{new_name}.csv'

        if os.path.exists(old_path):
            os.rename(old_path, new_path)
        else:
            return jsonify({'error': f"Board '{old_name}' does not exist."}), 404

        # Rename the image library folder if it exists
        old_image_path = f'./uploads/{old_name}'
        new_image_path = f'./uploads/{new_name}'

        if os.path.exists(old_image_path):
            os.rename(old_image_path, new_image_path)

        # Rename the backup file if it exists
        old_backup_path = f'./boards_data_backup/{old_name}.csv'
        new_backup_path = f'./boards_data_backup/{new_name}.csv'

        if os.path.exists(old_backup_path):
            os.rename(old_backup_path, new_backup_path)

        # Update references in other CSV files
        for filename in os.listdir('./boards_data'):
            if filename.endswith('.csv'):
                filepath = os.path.join('./boards_data', filename)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()

                updated_content = content.replace(old_name, new_name)

                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(updated_content)

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/delete_board', methods=['POST'])
def delete_board():
    try:
        # 删除本体
        board_name = request.json['board_name']
        os.remove(f'./boards_data/{board_name}.csv')

        # 删除备份
        if os.path.exists(f'./boards_data_backup/{board_name}.csv'): 
            os.remove(f'./boards_data_backup/{board_name}.csv')
        else: 
            pass

        # 删除上传的图片库
        if os.path.exists(f'./uploads/{board_name}'):
            # 强制删除图片库目录及其内容
            shutil.rmtree(f'./uploads/{board_name}')

            # 只能删除空目录
            # os.rmdir(f'./uploads/{board_name}')
        else:
            pass

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


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
    with open(f'./boards_data/{board_name}.csv', mode='r', newline='', encoding='utf-8', errors='ignore') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            cards.append(row)
    
    for row in cards:
        row[3] = str(int(row[3]) + int(top_change))  # 更新 top
        row[4] = str(int(row[4]) + int(left_change))  # 更新 left
    
    with open(f'./boards_data/{board_name}.csv', mode='w', newline='', encoding='utf-8', errors='ignore') as file:
        writer = csv.writer(file)
        writer.writerow(['CardID', 'CardName', 'CardContent', 'CardTop', 'CardLeft', 'CardWidth', 'CardHeight', 'CardBorderColor'])  # Add header
        writer.writerows(cards)


@app.route('/uploads/<board_name>/<timestamp>', methods=['POST'])
def save_image(board_name, timestamp):
    print(board_name)
    print(unquote(board_name))

    create_board_directory(board_name)
    
    if 'image' not in request.files:
        return '没有上传图片', 400
    
    image = request.files['image']
    save_path = os.path.join("uploads", board_name, f"{timestamp}.png")
    
    try:
        image.save(save_path)
        print("保存图片成功_savePath")
    except Exception as e:
        print("保存图片失败")
        return str(e), 500
    
    return '图片保存成功', 200


# 刚开始加载网页时，默认用的是GET，虽然没有写明白。
# 所以这里要补一个。
# @app.route('/uploads/<board_name>/<filename>.png', methods=['GET'])
# def uploaded_file(board_name, filename):
#     directory = f'uploads/{board_name}'
#     file_path = os.path.join(directory, f'{filename}.png')
    
#     if not os.path.exists(file_path):
#         print(file_path)
#         print(404)  # 文件不存在，返回404错误
#     else:
#         print("find it already.\n")
    
#     print("method is GET")
#     print(board_name)
#     print(unquote(board_name))
#     return send_from_directory(f'uploads/{board_name}',f'{filename}.png', mimetype='image/png')

@app.route('/uploads/<board_name>/<filename>.png', methods=['GET'])
def uploaded_file(board_name, filename):
    directory = os.path.abspath(os.path.join("uploads", board_name))  # Get absolute path
    file_path = os.path.join(directory, f'{filename}.png')

    if not os.path.exists(file_path):
        print(file_path)
        return 'File not found', 404

    return send_from_directory(directory, f'{filename}.png', mimetype='image/png')




def create_board_directory(board_name):
    path = os.path.join("uploads", board_name)
    if not os.path.exists(path):
        os.makedirs(path)


@app.route('/sync_content_with_image', methods=['POST'])
def sync_content_with_image():
    data = request.json
    card_id = data.get('card_ID')
    card_content = data.get('card_content')
    board_name = data.get('board_name')
    print(str(card_id))

    csv_path = f'./boards_data/{board_name}.csv'
    found = False
    with open(csv_path, mode='r', newline='', encoding='utf-8', errors='ignore') as file:
        reader = csv.reader(file)
        rows = list(reader)[1:] # Skip header
    
    for row in rows:  
        print(str(row[0]))
        if str(row[0]) == str(card_id):
            row[2] = card_content
            found = True
            break

    if not found:
        print(str(card_id))

    with open(csv_path, mode='w', newline='', encoding='utf-8', errors='ignore') as file:
        writer = csv.writer(file)
        writer.writerow(['CardID', 'CardName', 'CardContent', 'CardTop', 'CardLeft', 'CardWidth', 'CardHeight', 'CardBorderColor'])  # Add header
        writer.writerows(rows)

    return '内容同步成功', 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/get_content/<int:card_id>', methods=['GET'])
def get_content(card_id):
    board_name = request.args.get('board_name')  # 从查询参数中获取 board_name

    # 根据 board_name 构建 csv_path
    csv_path = f'./boards_data/{board_name}.csv'

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


@app.route('/delete_image', methods=['POST'])
def delete_image():
    try:
        data = request.get_json()
        imageSrc = unquote(data['imageSrc'])
        print("deleting the image:")
        print(imageSrc[22:])
        image_path = imageSrc[22:]

        if os.path.exists(image_path):
            os.remove(image_path)
            return jsonify({'status': 'success'}), 200, {'Content-Type': 'application/json; charset=utf-8'}
        else:
            return jsonify(error="Image not found"), 404, {'Content-Type': 'application/json; charset=utf-8'}
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500, {'Content-Type': 'application/json; charset=utf-8'}



if __name__ == '__main__':

    print(f"当前服务器工作路径: {os.getcwd()}")

    # 每1分钟进行数据备份 (无奈之举)
    # Start the backup thread
    backup_thread = threading.Thread(target=backup_boards_data, daemon=True)
    backup_thread.start()

    # 设置日志级别为 ERROR，只显示错误信息
    # log = logging.getLogger('werkzeug')
    # log.setLevel(logging.ERROR)

    # 获取默认浏览器可执行文件路径
    browser_path = webbrowser.get('windows-default' if os.name == 'nt' else 'default').name
    print(f"默认浏览器可执行文件路径: {browser_path}")
    # 打开浏览器访问指定网址（如果先启动Flask，就会卡在Flask的界面）
    webbrowser.open('http://127.0.0.1:5000')


    # 启动 Flask 应用
    # app.run()
    app.run(debug=True)
