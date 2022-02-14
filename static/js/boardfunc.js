var policeList = ['A','B','C','D','E']

// 更换地图
function changeMap(n){

    if (document.getElementById('displayloc').checked) {
        document.getElementById("img-map-loc").src="images/loc4.png";
    }
    else {
        document.getElementById("img-map-loc").src="images/alpha.png";
    }


    let map = document.getElementById("img-map");
    if (n == 1){
        map.src="images/vintage-map.jpg";
    }
    else if (n == 2){
        map.src="images/map_fix.jpg";
    }
    else if (n == 3){
        map.src="images/whitechapel-numbers-fix.jpg";
    }


    var alpha = document.getElementById("mapAlpha").value;
    if (alpha >=0 && alpha<=100){
        map.style.filter = 'alpha(opacity:'+alpha+')';
        map.style.opacity = alpha / 100;

    }

}

// 更新SVG
function refreshSVG() {
    let svg = document.getElementById("img-svg");

    if (document.getElementById('displaySVG').checked){

        svg.style.display = "";

        let alpha = document.getElementById("SVGAlpha").value;
        if (alpha >=0 && alpha<=100) {
            svg.style.filter = 'alpha(opacity:' + alpha + ')';
            svg.style.opacity = alpha / 100;
        }
    }
    else
        svg.style.display = "none";
}

// 绘制文字
function drawtext(canvas, text,x,y, maxWidth, color){
    var context = canvas.getContext('2d');

    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.font = 'bold '+maxWidth+'px Segoe UI Black';
    context.strokeStyle = '#ffffff';
    if (color){
        context.fillStyle = context.fillStyle = color;
        // context.fillStyle = '#f15151';
    }

    y += 1;
    // context.setTextSize(maxWidth);
    context.strokeText(text,x,y);
    context.fillText(text,x,y);
}

// function updatePointNumbers_log(canvas_1){
//     drawclear(canvas_1)
//
//     for (let i = 0; i < map.length; i++) {
//
//             // {#白点#}
//             if (map[i].number > 0) {
//                 [x, y] = coord(map[parseInt(i)].position);
//                 drawtext(canvas_1, map[i].number, x, y, 14, '#000000');
//
//             }
//
//
//         }
//
// }

// 创建div图标
function createDivImg(div, index, type, static=false, size= 1){

    if (parseInt(index) >= 0) {
        [x, y] = coord(map[parseInt(index)].position);
        z = 0
        alpha = 100

        if (type == 'mark'){
            name = 'mark'
            width = 60
            height = 90
            alpha = 80
        }
        else if (type == 'tragedy'){
            name = 'tragedy'
            width = 20
            height = 30
            alpha = 100
            y -= 5
        }
        else if (type == 'hidepolice'){
            name = 'police0'
            width = 20
            height = 30
            alpha = 100
            z = 10
            y -= 5
        }
        else if (type == 'footprint'){
            name = 'footprint1'
            width = 100
            height = 150
            alpha = 80
            y -= 5
        }
        else if (type == 'clueyellow'){
            name = 'clue2'
            width = 70
            height = 105
            alpha = 50
            z = -5
            y -= 3
        }
        else if (type == 'clue'){
            name = 'clue'
            width = 60
            height = 90
            alpha = 60
            y -= 3
        }
        else if (type == 'noclue'){
            name = 'clue4'
            width = 60
            height = 90
            alpha = 30
            y -= 3
        }
        else if (type == 'policeA' || type == 'policeB' || type == 'policeC' || type == 'policeD' || type == 'policeE'){
            name = type
            width = 20
            height = 30
            z = 10
            y -= 5
        }
        else if (type == 'policeAd' || type == 'policeBd' || type == 'policeCd' || type == 'policeDd' || type == 'policeEd'){
            name = type
            width = 20
            height = 30
            z = 10
            y -= 5
        }
        else if (type == 'jack'){
            name = 'jack'
            width = 20
            height = 30
            z = 20
            y -= 5
        }
        else if (type == 'home'){
            name = 'home'
            width = 40
            height = 60
            alpha = 80
            y -= 3
            z = -55
        }

        if (size<1){
            width = width * size
            height = height * size
            alpha = alpha * size
        }

        //创建一个div
        var img = document.createElement('img');
        let src = ''
        if (static)
            src = 'static/'
        src = src+'images/'+name+'.png'
        // console.log(src)
        img.setAttribute('src', src);
        img.setAttribute('width',width);
        img.setAttribute('height',height);
        img.setAttribute('name','temp');
        img.setAttribute('style','position:absolute; left:'+(x-width/2)+'px; top:'+(y-height/2)+'px;filter:alpha(Opacity='+alpha+');-moz-opacity:'+(alpha/100)+';opacity: '+(alpha/100)+';z-index: '+(z)+';');
        div.appendChild(img);

    }
}

// 清空div图标
function clearDIVtemp(usernameEle){

    var childs = usernameEle.childNodes;
    for(var i = childs.length - 1; i >= 0; i--) {
        usernameEle.removeChild(childs[i]);
    }

}

// 直线绘制
function drawline(canvas1, x1,y1,x2,y2,w,color, ran){

    // 拿到上下文
    var context = canvas1.getContext('2d');
    // 设置线条的颜色
    context.strokeStyle = color;
    // 设置线条的宽度
    context.lineWidth = w;

    // 绘制直线
    context.beginPath();
    // 起点
    context.moveTo(x1+ran*(Math.random()-0.5), y1+ran*(Math.random()-0.5));
    // 终点
    context.lineTo(x2+ran*(Math.random()-0.5), y2+ran*(Math.random()-0.5));
    context.closePath();
    context.stroke();

}

// 清空画布
function drawclear(canvas){
    var context = canvas.getContext('2d');
    context.clearRect(0,0,1448,960);
}