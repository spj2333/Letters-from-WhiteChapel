function drag(obj) { //封装函数
    obj.onmousedown = function(ev) { //鼠标点击需要拖动的元素执行的函数
        var ev = ev || event; //事件的浏览器兼容性
        var disX = ev.clientX - this.offsetLeft; //鼠标到拖拽元素左侧的距离=鼠标当前距离浏览器左侧的距离-拖动元素左侧距离浏览器左侧的距离
        var disY = ev.clientY - this.offsetTop; //鼠标到拖拽元素顶部的距离=鼠标当前距离浏览器顶部的距离-拖动元素顶部距离浏览器顶部的距离
        if (obj.setCapture) { //如果存在setCapture()说明是IE678，所以需要设置全局捕获来阻止拖拽时的默认行为
            obj.setCapture();
        }

        document.onmousemove = function(ev) { //当鼠标移动的时候执行的函数
            var ev = ev || event; //事件的浏览器兼容性
            obj.style.left = ev.clientX - disX + 'px'; //拖动元素左侧的位置=当前鼠标距离浏览器左侧的距离 - （物体宽度的一半）
            obj.style.top = ev.clientY - disY + 'px'; //拖动元素顶部的位置
        }

        document.onmouseup = function() { //鼠标放开时执行的函数
            document.onmousemove = document.onmouseup = null; //清空鼠标移动时的函数
            if (obj.releaseCapture) { //如果存在releaseCapture()说明是IE678，所以需要解除刚才设置的全局捕获
                obj.releaseCapture();
            }
        }

        return false; //取消文字选择的默认行为
    }

}