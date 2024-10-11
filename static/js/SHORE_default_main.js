// =================================
// FUNC I  全局拖动 (所有卡片)与拖动单个卡片
// =================================
// 
let isWholeSpaceDragging = false;
let spaceOffsetX, spaceOffsetY;

// 存储所有卡片的初始位置
const cards = Array.from(document.querySelectorAll('.card'));
const cardPositions = cards.map(card => ({
    card,
    left: parseFloat(card.style.left),
    top: parseFloat(card.style.top)
}));

 document.addEventListener('keydown', (e) => {
     if (e.code === 'Space' 
         && document.activeElement.className !== 'content'
         && document.activeElement.className !== 'name'
        //  && document.activeElement.className !== 'originLATEX'
        //  && document.activeElement.className !== 'originLATEX_inline'
         ) {
         e.preventDefault();
         isWholeSpaceDragging = !isWholeSpaceDragging; // Toggle dragging
         document.body.style.userSelect = isWholeSpaceDragging ? 'none' : '';
         document.body.style.cursor = isWholeSpaceDragging ? 'grab' : ''; // Change cursor
         if (!isWholeSpaceDragging) {
             document.removeEventListener('mousemove', dragAllCards); // Stop dragging if toggled off
         }
     }
 });

document.addEventListener('mousedown', (e) => {
    if (isWholeSpaceDragging) {
        spaceOffsetX = e.clientX;
        spaceOffsetY = e.clientY;
        document.addEventListener('mousemove', dragAllCards);
    }
});


document.addEventListener('mouseup', (e) => {
    if (isWholeSpaceDragging) {
        document.removeEventListener('mousemove', dragAllCards);
        const topChange = e.clientY - spaceOffsetY;
        const leftChange = e.clientX - spaceOffsetX;
        
        // 更新初始位置
        cardPositions.forEach(pos => {
            pos.left += leftChange;
            pos.top += topChange;
        });

        adjustBodySize();

        fetch('/move_all_cards', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json; charset=UTF-8'
            },
            body: JSON.stringify({ 
                board_name: currentBoardName,
                top_change: topChange,
                left_change: leftChange,
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {  // 更新以匹配后端响应
                alert(data.error);
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            alert('An error occurred while moving the cards. Please try again.');
        });
    }
});

let isDragging = false;
let offsetX, offsetY, currentCard;

function startDrag(e, card) {
    isDragging = true;
    currentCard = card;
    offsetX = e.clientX - card.offsetLeft;
    offsetY = e.clientY - card.offsetTop;
    document.body.style.userSelect = 'none';
}

function drag(e) {
    if (isDragging && currentCard) {
        const left = e.clientX - offsetX;
        const top = e.clientY - offsetY;
        currentCard.style.left = left + 'px';
        currentCard.style.top = top + 'px';
    }
}

function stopDrag(e) {
    if (isDragging) {
        isDragging = false;
        const cardID = currentCard.id;
        const cardLeft = currentCard.style.left;
        const cardTop = currentCard.style.top;

        // 更新 cardPositions 数组中的位置
        const index = cardPositions.findIndex(pos => pos.card.id === cardID);
        if (index !== -1) {
            cardPositions[index].left = parseFloat(cardLeft);
            cardPositions[index].top = parseFloat(cardTop);
        }

        adjustBodySize();

        fetch('/update_card', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json; charset=UTF-8'
            },
            body: JSON.stringify({ 
                board_name: currentBoardName,
                card_id: cardID, 
                left: cardLeft, 
                top: cardTop, 
            })
        })
        .then(response => response.json())
        // .then(data => {
        //     console.log('Success:', data);
        // })
        .catch((error) => {
            console.error('Error:', error);
        });
    }
    document.body.style.userSelect = '';
}

function dragAllCards(e) {
    const deltaX = e.clientX - spaceOffsetX;
    const deltaY = e.clientY - spaceOffsetY;
    cardPositions.forEach(pos => {
        const newLeft = pos.left + deltaX;
        const newTop = pos.top + deltaY;
        pos.card.style.left = newLeft + 'px';
        pos.card.style.top = newTop + 'px';
    });

}



// =================================
// FUNC II  无限卷轴 (画布扩展)
// =================================
function adjustBodySize() {
    const body = document.body;

    const maxRight = Math.max(...cardPositions.map(pos => pos.left + pos.card.offsetWidth));
    const maxBottom = Math.max(...cardPositions.map(pos => pos.top + pos.card.offsetHeight));

    // Add extra space
    const extraSpace = 100; // Adjust this value for more or less space
    body.style.width = (maxRight + extraSpace) + 'px';
    body.style.height = (maxBottom + extraSpace) + 'px';
}


// =================================
// FUNC III  核心函数 —— 保存卡片contentArea的内容(及样式)
// =================================
function updateCardContent(contentArea) {
    const card = contentArea.parentElement;
    const card_id = card.id;
    const contentValue = contentArea.value;
    const name = card.querySelector('.name').value;
    const previewArea   = contentArea.closest('.card').querySelector('.preview');
    let heightToBackend = previewArea.scrollHeight === 0 ? card.style.height :`${previewArea.scrollHeight + 34}px`; 
    console.log(heightToBackend)

    // console.log(contentValue)
    // console.log(contentArea.className)
    // console.log(contentArea.tagName)
    console.log(`updating card: ${card_id}`);

    // 发送更新数据到服务器
    fetch('/update_card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json; charset=UTF-8'
        },
        body: JSON.stringify({
            board_name: currentBoardName,
            card_id: card_id,
            content: contentValue,
            name: name,
            height: heightToBackend,
        })
    })
    .then(response => response.json())
    .catch((error) => {
        console.error('Error: updateContent数据同步失败。', error);
    });
}

// III.1 调整卡片长和宽
// ---------------------------------
document.querySelectorAll('.card-resize-handle').forEach(handle => {
    handle.addEventListener('mousedown', (e) => {
        e.stopPropagation(); // Prevent event bubbling
        document.body.style.userSelect = 'none'; // Disable text selection

        const card = handle.parentElement;
        const startX = e.clientX;
        const startY = e.clientY;
        const startWidth = card.offsetWidth;
        const startHeight = card.offsetHeight;

        function onMouseMove(e) {
            const newWidth = startWidth + (e.clientX - startX);
            const newHeight = startHeight + (e.clientY - startY);
            card.style.width = newWidth + 'px';
            card.style.height = newHeight + 'px';
        }

        function onMouseUp() {
            const id = card.id;
            // const left = card.style.left;
            // const top = card.style.top;
            // const name = card.querySelector('.name').value;
            const width = card.style.width;
            const height = parseInt(card.getBoundingClientRect().height);
            console.log("Resizing card.")
            console.log("width",width)
            console.log("height",height)

            // Send updated data to the server
            fetch('/update_card', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json; charset=UTF-8'
                },
                body: JSON.stringify({ board_name: currentBoardName, card_id: id, width: width, height: height })
            })
            .then(response => response.json())
            // .then(data => {
            //     console.log('Success:', data);
            // })
            .catch((error) => {
                console.error('Error:', error);
            });

            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });
});

// III.2 输入更新卡片的Name行
// ---------------------------------
function updateName(input) {
    const card = input.closest('.card'); // 获取 card
    const card_id = card.id;
    const name = input.value;
    // 发送更新数据到服务器
    fetch('/update_card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json; charset=UTF-8'
        },
        body: JSON.stringify({ 
            board_name: currentBoardName, 
            card_id: card_id, 
            name: name,
        })
    })
    .then(response => response.json())
    .catch((error) => {
        console.error('Error:', error);
    });
}

// III.3 提示用户用 Ctrl+S 保存。
// ---------------------------------
const notification = document.getElementById('notification');

// Show notification on focusin
document.addEventListener('focusin', function(event) {
    if (event.target.classList.contains('content')) {
        notification.style.animation = 'fadeIn 1s ease';
        notification.style.display = 'block';

        // Hide notification after 3 seconds (3000 ms)
        setTimeout(function() {
            notification.style.display = 'none';
        }, 3000);
    }
});



// =================================
// FUNC IV  在卡片contentArea 中处理图片和 markdown与LaTeX
// =================================

// IV.1  图片粘贴处理（上传与保存）以及无格式粘贴
// ---------------------------------
document.querySelectorAll('.content').forEach(contentArea => {
    contentArea.addEventListener('paste', async function(event) {
        event.preventDefault(); // 阻止默认粘贴行为
        const items = event.clipboardData.items;
        const hasImages = Array.from(items).some(item => item.type.startsWith('image/'));

        if (hasImages) {
            const imagePromises = [];
            for (const item of items) {
                if (item.type.startsWith('image/')) {
                    const file = item.getAsFile();
                    const formData = new FormData();
                    const timestamp = Date.now();
                    formData.append('image', file, `${timestamp}.png`);

                    const uploadPromise = fetch(`/uploads/${currentBoardName}/${timestamp}`, {
                        method: 'POST',
                        body: formData
                    }).then(response => {
                        if (response.ok) {
                            const imgHTML = `<div style="text-align: center;"><div class="img-container" style="position: relative;"><img src="/uploaded_images/${currentBoardName}/${timestamp}.png" class="normal-image" alt="粘贴的图片" style="display: block; box-shadow: rgba(0, 0, 0, 0.5) 1px 1px 3px;"><div class="img-resize-handle" style="background-color: black;"></div></div></div>`;
                            insertAtCursor(this, imgHTML); // 将 imgHTML 作为文本插入
                        }
                    });
                    imagePromises.push(uploadPromise);
                }
            }
            await Promise.all(imagePromises);
            updateCardContent(contentArea);
        } else {
            // 处理普通文本或格式化文本粘贴
            const text = await navigator.clipboard.readText();
            insertAtCursor(this, text); // 正常粘贴文本
        }
    });

    function insertAtCursor(el, text) {
        const cursorPosition = el.selectionStart;
        const currentText = el.value;

        // 将文本插入到光标位置
        el.value = currentText.slice(0, cursorPosition) + text + currentText.slice(cursorPosition);
        
        // 更新光标位置
        el.selectionStart = el.selectionEnd = cursorPosition + text.length;
    }

});

// IV.2  图片右键删除处理
// ---------------------------------
// 补充：注意不要有 headers，也不需要设置utf-8
let previousImages = [];
setInterval(() => {
    const currentImages = Array.from(document.querySelectorAll('img'));
    
    if (currentImages.length < previousImages.length) {
        previousImages.forEach(src => {
            if (!currentImages.some(img => img.src === src)) {
                const decodedSrc = decodeURIComponent(src);
                console.log(`Image deleted: ${decodedSrc}`);
                fetch('/delete_image', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8'
                    },
                    body: JSON.stringify({ imageSrc: src })
                });
            }
        });
    }
    
    previousImages = currentImages.map(img => img.src);
}, 500);


// =================================
// FUNC V  菜单——在空白处右键
// =================================
document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    const menu = document.getElementById('context-menu');
    const cardMenu = document.getElementById('card-context-menu');
    
    if (e.target.classList.contains('card') || e.target.classList.contains('name')) {
        const cardId = e.target.closest('.card').id;
        cardMenu.style.left = `${e.pageX}px`;
        cardMenu.style.top = `${e.pageY}px`;
        cardMenu.style.display = 'block';
        cardMenu.dataset.cardId = cardId;

    } else {
        menu.style.left = `${e.pageX}px`;
        menu.style.top = `${e.pageY}px`;
        menu.style.display = 'block';
    }
});

// 创建新卡片的事件
document.getElementById('create-card').addEventListener('click', (e) => {
    const newCardId = Date.now(); 
    const menu = document.getElementById('context-menu');

    // console.log(`${e.pageX}px`)
    // console.log(`${e.pageY}px`)

    fetch('/add_card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json; charset=UTF-8'
        },
        body: JSON.stringify({ 
            board_name: currentBoardName, 
            card_id: newCardId, 
            content: '新卡片内容',
            left: `${e.pageX - 100}`,
            top: `${e.pageY - 10}`,
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success: Adding Card', data);
        location.reload();
    })
    .catch((error) => {
        console.error('Error:', error);
    });

    document.getElementById('context-menu').style.display = 'none'; 
});

// 点击空白处隐藏菜单
document.addEventListener('click', () => {
    document.getElementById('context-menu').style.display = 'none';
    document.getElementById('card-context-menu').style.display = 'none';
});



// =================================
// FUNC VI  菜单——在卡片上右键
// =================================
let activeLatexElement = null; // 用于保存当前活动的LaTeX元素 或者 图片元素

document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    const card = e.target.closest('.card');
    const menu = document.getElementById('card-context-menu');
    const latexElement = e.target.closest('.originLATEX, .originLATEX_inline'); // 检查是否在 LaTeX 元素上
    const imgElement = e.target.closest('img'); // 检查是否在图像元素上

    if (card) {
        const cardId = card.id; 
        menu.style.left = `${e.pageX}px`;
        menu.style.top = `${e.pageY}px`;
        menu.style.display = 'block';
        const divs = menu.querySelectorAll('div'); // 获取所有子元素的div
        divs.forEach(div => {
            div.style.display = '';
        });

        // 处理图像对齐方式的逻辑
        if (imgElement && imgElement.classList.contains('normal-image')) {
            activeImageElement = imgElement; // 保存当前活动的图像元素
            const alignmentMenu = document.getElementById('change-image-alignment');
            
            divs.forEach(div => {
                div.style.display = 'none'; // 隐藏其他选项
            });
            alignmentMenu.style.display = 'block'; // 显示更改对齐选项
            alignmentMenu.innerHTML = ''; // 清空之前的事件处理器

            // 创建对齐方式选项
            const alignments = ['left', 'center', 'right'];
            alignments.forEach(alignment => {
                const button = document.createElement('button');
                button.textContent = alignment === 'center' ? '居中' : `靠${alignment === 'left' ? '左' : '右'}`;
                button.classList.add('alignment-button');
                button.onclick = function() {
                    const imgContainer = imgElement.closest('.img-container');
                    if (imgContainer) {
                        let HTML_before = imgContainer.parentElement.outerHTML;
                        imgContainer.parentElement.style.textAlign = alignment; // 更新对齐方式
                        let HTML_after  = imgContainer.parentElement.outerHTML;
                        
                        let contentElement = imgElement.closest('.card').querySelector('.content');
                        let contentValue = contentElement.value;
                        let updatedContent = contentValue.replace(HTML_before, HTML_after);
                        contentElement.value = updatedContent;

                        updateCardContent(contentElement);
                    }
                    alignmentMenu.style.display = 'none'; // 隐藏对齐选项
                };
                alignmentMenu.appendChild(button);
            });

            // 添加删除图像的逻辑
            const deleteImageButton = document.getElementById('delete-normal-image');
            deleteImageButton.style.display = 'block'; // 显示删除图像选项
            deleteImageButton.onclick = function() {
                const imgContainer = imgElement.closest('.img-container');
                if (imgContainer) {
                    const confirmDelete = confirm('确定要删除这张图片吗？');
                    if (confirmDelete) {
                        console.log('确定要删除这张图片吗？')
                        let contentElement = imgElement.closest('.card').querySelector('.content');
                        let contentValue = contentElement.value;
                        // 获取图片容器的 outerHTML
                        let imgOuterHTML = imgContainer.parentElement.outerHTML;
                        // 将图片容器的 outerHTML 从 content 中删除
                        let updatedContent = contentValue.replace(imgOuterHTML, '');
                        contentElement.value = updatedContent;
                        updateCardContent(contentElement)
                        console.log('图片及其容器已从内容框中删除');

                        // 删除图像的父元素
                        imgContainer.parentElement.remove(); 
                    }
                }
                menu.style.display = 'none'; 
            };

            // // 添加复制图像到剪贴板的逻辑 
            // const copyImageButton = document.getElementById('copy-image-to-clipboard');
            // copyImageButton.style.display = 'block'; // 显示复制图像选项
            // // console.log(copyImageButton.style.display);
            // copyImageButton.onclick = function() {
            //     const imgSrc = imgElement.src; // 获取图像的src
            //     const imgAlt = imgElement.alt || ''; // 获取图像的alt文本（如果有）
            //     const imgWidth = imgElement.width || ''; // 获取图像的宽度
            //     const imgHeight = imgElement.height || ''; // 获取图像的高度

            //     // 创建 HTML 格式的图像字符串
            //     const imgHTML = `
            //         <div class="img-container" style="position: relative;">
            //             <img src="${imgSrc}" alt="${imgAlt}" class="normal-image" 
            //                 style="display: block; box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);" 
            //                 width="${imgWidth}" height="${imgHeight}">
            //             <div class="img-resize-handle" style="background-color: black;"></div>
            //         </div>
            //     `;

            //     // 创建一个临时的 textarea 用于复制
            //     const tempTextarea = document.createElement('textarea');
            //     tempTextarea.value = imgHTML; // 使用 HTML 格式
            //     document.body.appendChild(tempTextarea);
            //     tempTextarea.select();
            //     document.execCommand('copy'); // 复制到剪贴板
            //     document.body.removeChild(tempTextarea); // 移除临时元素
                
            //     // 创建提示信息
            //     const notification = document.createElement('div');
            //     notification.innerText = '图像已复制到剪贴板！';
            //     notification.style.position = 'fixed';
            //     notification.style.bottom = '20px';
            //     notification.style.right = '20px';
            //     notification.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            //     notification.style.color = 'white';
            //     notification.style.padding = '10px';
            //     notification.style.borderRadius = '5px';
            //     notification.style.zIndex = '1000';
            //     document.body.appendChild(notification);

            //     // 自动消失
            //     setTimeout(() => {
            //         document.body.removeChild(notification);
            //     }, 1500); // 1.5秒后消失

            //     // alert('图像已复制到剪贴板！');
            //     menu.style.display = 'none'; 
            // };


        } 
        // else if (latexElement) {
        //     activeLatexElement = latexElement; // 保存当前活动的 LaTeX 元素
        //     divs.forEach(div => {
        //         div.style.display = 'none'; // 隐藏其他选项
        //     });
        //     document.getElementById('delete-latex').style.display = 'block'; // 显示删除 LaTeX 选项
            
        //     document.getElementById('delete-latex').onclick = function() {
        //         if (activeLatexElement) {
        //             const confirmDelete = confirm('确定要删除这段LaTeX吗？');
        //             if (confirmDelete) {
        //                 // 检查父元素的类型 (整行公式渲染完还有一个span套在外面)
        //                 if (activeLatexElement.parentElement && activeLatexElement.parentElement.tagName === 'SPAN') {
        //                     activeLatexElement.parentElement.remove();
        //                 } else {
        //                     // 如果是行内公式
        //                     activeLatexElement.remove(); // 删除最近的LaTeX元素
        //                 }
        //                 activeLatexElement = null; // 清除引用
        //             }
        //         }
        //         menu.style.display = 'none'; 
        //     };

        //     // 复制LaTex 的输入到剪贴板
        //     document.getElementById('copy-latexInput-to-clipboard').style.display = 'block';
        //     document.getElementById('copy-latexInput-to-clipboard').onclick = function() {
        //         if (activeLatexElement) {
        //             const latexInput = activeLatexElement.querySelector('annotation').innerHTML; // 获取 LaTeX 输入

        //             // 创建一个临时的 textarea 用于复制
        //             const tempTextarea = document.createElement('textarea');
        //             tempTextarea.value = latexInput; // 设置为 LaTeX 输入
        //             document.body.appendChild(tempTextarea);
        //             tempTextarea.select();
        //             document.execCommand('copy'); // 复制到剪贴板
        //             document.body.removeChild(tempTextarea); // 移除临时元素

        //             // 创建提示信息
        //             const notification = document.createElement('div');
        //             notification.innerText = 'LaTeX 输入已复制到剪贴板！';
        //             notification.style.position = 'fixed';
        //             notification.style.bottom = '20px';
        //             notification.style.right = '20px';
        //             notification.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        //             notification.style.color = 'white';
        //             notification.style.padding = '10px';
        //             notification.style.borderRadius = '5px';
        //             notification.style.zIndex = '1000';
        //             document.body.appendChild(notification);

        //             // 自动消失
        //             setTimeout(() => {
        //                 document.body.removeChild(notification);
        //             }, 1500); // 1.5秒后消失
        //         }
        //     };


        //     // 复制LaTeX HTML渲染结果到剪贴板
        //     document.getElementById('copy-latexHTML-to-clipboard').style.display = 'block';
        //     document.getElementById('copy-latexHTML-to-clipboard').onclick = function() {
        //         console.log("复制 LaTeX 渲染结果");
        //         if (activeLatexElement) {
        //             let latexHTML;

        //             // 检查父元素的类型 (整行公式渲染完还有一个span套在外面)
        //             if (activeLatexElement.parentElement && activeLatexElement.parentElement.tagName === 'SPAN') {
        //                 latexHTML = `<br><div>${activeLatexElement.parentElement.outerHTML}</div><br>`; // 使用父元素的 outerHTML
        //             } else {
        //                 latexHTML = activeLatexElement.outerHTML; // 使用行内公式的 outerHTML
        //             }

        //             // 创建一个临时的 textarea 用于复制
        //             const tempTextarea = document.createElement('textarea');
        //             tempTextarea.value = latexHTML; // 使用 HTML 格式
        //             document.body.appendChild(tempTextarea);
        //             tempTextarea.select();
        //             document.execCommand('copy'); // 复制到剪贴板
        //             document.body.removeChild(tempTextarea); // 移除临时元素

        //             // 创建提示信息
        //             const notification = document.createElement('div');
        //             notification.innerText = '公式渲染结果 已复制到剪贴板！';
        //             notification.style.position = 'fixed';
        //             notification.style.bottom = '20px';
        //             notification.style.right = '20px';
        //             notification.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        //             notification.style.color = 'white';
        //             notification.style.padding = '10px';
        //             notification.style.borderRadius = '5px';
        //             notification.style.zIndex = '1000';
        //             document.body.appendChild(notification);

        //             // 自动消失
        //             setTimeout(() => {
        //                 document.body.removeChild(notification);
        //             }, 1500); // 1.5秒后消失

        //             activeLatexElement = null; // 清除引用
        //         }
        //         menu.style.display = 'none';
        //     };


        // } 
        else {
            divs.forEach(div => {
                div.style.display = ''; // 显示所有选项
            });
            document.getElementById('change-image-alignment').style.display = 'none'; // 隐藏对齐选项
            // document.getElementById('delete-latex').style.display = 'none'; // 隐藏删除选项
            document.getElementById('delete-normal-image').style.display = 'none';
            // document.getElementById('copy-image-to-clipboard').style.display = 'none';
            // document.getElementById('copy-latexHTML-to-clipboard').style.display = 'none';
            // document.getElementById('copy-latexInput-to-clipboard').style.display = 'none';
        }

        // 点击删除卡片选项
        document.getElementById('delete-card').onclick = function() {
            card.remove(); 
            fetch('/delete_card', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json; charset=UTF-8'
                },
                body: JSON.stringify({ board_name: currentBoardName, card_id: cardId })
            });
            menu.style.display = 'none'; 
        };


        // 设置z轴
        const setZIndexButton = document.getElementById('set-z-index');
        setZIndexButton.addEventListener('click', function handleClick() {
            let zIndex = card.style.zIndex || window.getComputedStyle(card).zIndex;
            const customZValue = prompt(`当前Z值是 ${zIndex}. 请输入自定义Z值`, zIndex);
            if (customZValue !== null) {
                card.style.zIndex = customZValue;

                // 发送请求更新 z_index
                fetch('/update_card', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json; charset=UTF-8'
                    },
                    body: JSON.stringify({
                        board_name: currentBoardName,
                        card_id: cardId,
                        z_index: customZValue
                    })
                });
            }
            // Optionally remove the event listener to prevent multiple prompts
            setZIndexButton.removeEventListener('click', handleClick);
        });

        // 绑定点击事件到复制按钮
        document.getElementById('copy-that-card').onclick = function() {
            const cardToCopy = document.getElementById(cardId); // Get the card to copy

            // Clone the card
            const newCard = cardToCopy.cloneNode(true); // Clone the card and its contents
            const newCardId = Date.now(); // Generate a new unique ID
            newCard.id = newCardId; // Assign the new ID
            newCard.style.left = (parseInt(cardToCopy.style.left) + 20) + 'px'; // Adjust left position
            newCard.style.top = (parseInt(cardToCopy.style.top) + 20) + 'px'; // Adjust top position
            newCard.style.width = cardToCopy.style.width;
            newCard.style.height = (parseInt(cardToCopy.style.height) + 20) + 'px'; 
            newCard.style.borderTopColor = cardToCopy.style.borderTopColor;
            const cardName = cardToCopy.querySelector('input').value; // 获取 Name
            newCard.style.zIndex = cardToCopy.style.zIndex;

            let height_not_px = newCard.style.height;

            if (height_not_px.endsWith('px')) {
                height_not_px = height_not_px.replace('px', ''); // 去掉 px
            }


            // Send new card data to the server
            fetch('/add_card', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json; charset=UTF-8'
                },
                body: JSON.stringify({ 
                    board_name: currentBoardName, 
                    card_id: newCardId, 
                    card_name: cardName,
                    content: cardToCopy.querySelector('.content').innerHTML, // Copy the content
                    top: newCard.style.top.replace('px', ''), // Get top value
                    left: newCard.style.left.replace('px', ''), // Get left value
                    width: newCard.style.width.replace('px', ''), // Get width
                    height: height_not_px, // Get height
                    color: newCard.style.borderTopColor, // Get border color
                    z_index: newCard.style.zIndex,
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Success: Copying Card', data);
                location.reload(); // Reload to update the view
            })
            .catch((error) => {
                console.error('Error:', error);
            });

            menu.style.display = 'none'; // Hide the context menu
        };

        // 自定义颜色输入
        document.getElementById('change-color').onclick = function() {
            const customColor = prompt("请输入自定义颜色（例如: #ff0000，darkred，transparent）:");
            if (customColor) {
                card.style.borderTopColor = customColor; // Apply color to the targeted card
                const resizeHandle = card.querySelector('.card-resize-handle');
                if (resizeHandle) {
                    resizeHandle.style.backgroundColor = customColor; // Change color of resize handle
                }

                fetch('/update_card', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json; charset=UTF-8'
                    },
                    body: JSON.stringify({ 
                        board_name: currentBoardName, 
                        card_id: cardId, 
                        color: customColor 
                    })
                });
            }
        };

        // 颜色选择功能
        const colorCircles = document.querySelectorAll('.color-circle');
        colorCircles.forEach(circle => {
            circle.onclick = function() {
                const newColor = this.style.backgroundColor;
                card.style.borderTopColor = newColor; // Apply color to the targeted card
                const resizeHandle = card.querySelector('.card-resize-handle');
                if (resizeHandle) {
                    resizeHandle.style.backgroundColor = newColor; // Change color of resize handle
                }

                fetch('/update_card', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json; charset=UTF-8'
                    },
                    body: JSON.stringify({ 
                        board_name: currentBoardName, 
                        card_id: cardId, 
                        color: newColor 
                    })
                });
            };
        });
    } else {
        document.getElementById('context-menu').style.left = `${e.pageX}px`;
        document.getElementById('context-menu').style.top = `${e.pageY}px`;
        document.getElementById('context-menu').style.display = 'block';
    }
});


// 更新卡片高度的函数
function updateHeight_Img(contentArea) {
    const card = contentArea.parentElement;
    const previewArea = contentArea.closest('.card').querySelector('.preview');
    const images = previewArea.querySelectorAll('img');
    
    // Calculate total height including images
    let totalHeight = contentArea.scrollHeight + Array.from(images).reduce((sum, img) => sum + img.offsetHeight, 0);

    let heightToBackend = totalHeight === 0 ? card.style.height : `${totalHeight + 34}px`;
    console.log("正在使用 updateHeight_Img函数, height is ", heightToBackend);

    // previewArea.style.height = `${heightToBackend - 34}px`;
    card.style.height = `${heightToBackend}px`;

    fetch('/update_card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json; charset=UTF-8'
        },
        body: JSON.stringify({ 
            board_name: currentBoardName,
            card_id: card.id, 
            height: `${heightToBackend}px`,
        })
    })
    .then(response => response.json())
    .catch(error => {
        console.error('Error:', error);
    });
}




// =================================
// FUNC VII  "主函数" —— DOM加载完成后的命令。
// =================================
// 页面加载完成后，运行
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        const contentArea = card.querySelector('.content');
        // contentArea.style.height = 'auto';
        // contentArea.style.height = contentArea.scrollHeight + 'px';
        renderContent(contentArea);

        card.addEventListener('mousedown', (e) => {
            if (!e.target.classList.contains('content')) {
                startDrag(e, card);
            }
        });
    });

    // 添加调整大小的功能到所有图片
    const allImages = document.querySelectorAll('img');
    allImages.forEach(img => {
        const imgContainer = img.closest('.img-container'); // 假设每个图像都有一个父容器
        const handle = imgContainer.querySelector('.img-resize-handle'); // 假设有一个调整大小的句柄
        if (handle) {
            addImageResizeFunctionality(handle, img, imgContainer);
        }
    });

    document.addEventListener('mouseup', stopDrag);
    document.addEventListener('mousemove', drag);

    document.addEventListener('keydown', function(event) {
        if (event.ctrlKey && event.key === 's') {
            event.preventDefault(); // Prevent the default save action
            const focusedElement = document.activeElement;

            if (focusedElement.classList.contains('content')) {
                const contentArea = focusedElement;
                const previewArea = contentArea.closest('.card').querySelector('.preview');
                // const previewArea = focusedElement.closest('.card').querySelector('.preview');
                renderContent(contentArea);
                updateHeight_Img(contentArea);
                updateCardContent(contentArea);
                contentArea.closest('.card').style.height = "fit-content";
                console.log(contentArea.closest('.card').style.height);

                const tmp_height = parseInt(contentArea.closest('.card').getBoundingClientRect().height);
                console.log("tmp_height is ",tmp_height)
                contentArea.closest('.card').style.height = `${tmp_height}px`;   
                console.log(contentArea.closest('.card').style.height);

            }
        }
    });

    adjustBodySize();
});

function renderContent(contentArea) {
    const previewArea = contentArea.closest('.card').querySelector('.preview');

    // Save modifications to the backend
    updateCardContent(contentArea);

    // Render Markdown content using marked.js
    const htmlContent = marked(contentArea.value);
    if(htmlContent === ""){
        previewArea.innerHTML = "<br>Empty Space.<br>";
    }else{
        previewArea.innerHTML = htmlContent; // Render to preview area
    }

    // Render math using KaTeX
    renderMathInElement(previewArea, {
        delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false }
        ]
    });

    // Highlight code blocks using highlight.js
    const codeBlocks = previewArea.querySelectorAll('pre code');
    codeBlocks.forEach((block) => {
        // hljs.highlightBlock(block); 
        // Perform highlighting
        hljs.highlightElement(block);
    });

    // Toggle visibility
    previewArea.style.display = 'block';
    contentArea.style.display = 'none';

    // Toggle visibility of content and preview on double-click
    previewArea.addEventListener('dblclick', function () {
        previewArea.style.display = 'none';
        contentArea.style.display = 'block';
    });

    // 添加调整大小的功能到所有图像
    const imageResizeHandles = previewArea.querySelectorAll('.img-resize-handle');
    imageResizeHandles.forEach(handle => {
        const imgContainer = handle.closest('.img-container');
        const img = imgContainer.querySelector('img');
        addImageResizeFunctionality(handle, img, imgContainer);
    });
}

function addImageResizeFunctionality(handle, img, imgContainer) {
    // console.log("正在加呢！")
    handle.addEventListener('mousedown', (e) => {
        e.stopPropagation();
        document.body.style.userSelect = 'none';
        // handle.style.display = 'block'
        let HTML_before = imgContainer.parentElement.outerHTML;

        const startX = e.clientX;
        // const startY = e.clientY;
        const startWidth = img.offsetWidth;
        const startHeight = img.offsetHeight;
        const aspectRatio = startWidth / startHeight;

        function onMouseMove(e) {
            const newWidth = Math.max(50, startWidth + (e.clientX - startX)); // Prevent shrinking too small
            const newHeight = newWidth / aspectRatio; // Maintain aspect ratio
            img.style.width = newWidth + 'px';
            img.style.height = newHeight + 'px';
            imgContainer.dataset.width = newWidth;
            imgContainer.dataset.height = newHeight;
        }

        function onMouseUp() {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            handle.style.display = ''

            let HTML_after  = imgContainer.parentElement.outerHTML;
            let contentElement = img.closest('.card').querySelector('.content');
            let contentValue = contentElement.value;
            // console.log(HTML_before)
            // console.log(HTML_after)
            // console.log(contentValue)

            if (contentValue.includes(HTML_before)) {
                let updatedContent = contentValue.replace(HTML_before, HTML_after);
                contentElement.value = updatedContent;
                updateCardContent(contentElement);
            } else {
                console.log("No match found for HTML_before in contentValue.");
            }            
            updateCardContent(contentElement);

        }

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });
}

// ===========================
// 补充一些功能 v0.4.6B
// ===========================
// 获取所有textarea元素，增加对`Alt+Enter`的支持。
const textareas = document.querySelectorAll('textarea');

textareas.forEach(textarea => {
    textarea.addEventListener('keydown', function (event) {
        // 判断是否按下了 Alt + Enter
        if (event.altKey && event.key === 'Enter') {
            event.preventDefault(); // 阻止默认换行行为

            // 获取光标位置
            const cursorPosition = textarea.selectionStart;
            
            // 获取textarea的值
            const textValue = textarea.value;
            
            // 在光标位置插入 <br>
            const newValue = textValue.substring(0, cursorPosition) + '<br>' + textValue.substring(cursorPosition);
            
            // 更新textarea的值
            textarea.value = newValue;
            
            // 将光标定位到插入后的正确位置
            textarea.setSelectionRange(cursorPosition + 4, cursorPosition + 4); // 光标移动到 <br> 后面
        }
    });
});
