function voice(ttsText){
    var utterThis = new window.SpeechSynthesisUtterance()
    utterThis.text = ttsText
    utterThis.rate = 2
    window.speechSynthesis.speak(utterThis)
    }


    // function voice(ttsText){
    //
    // var ttsDiv = document.getElementById('bdtts_div_id');
    // var ttsAudio = document.getElementById('tts_autio_id');
    //
    // ttsDiv.removeChild(ttsAudio);
    // var au1 = '<audio id="tts_autio_id" autoplay="autoplay">';
    // var sss = '<source id="tts_source_id" src="https://tts.baidu.com/text2audio?lan=zh&ie=UTF-8&per=3&spd=8&text=' + ttsText + '" type="audio/mpeg">';
    // var eee = '<embed id="tts_embed_id" height="0" width="0" src="">';
    // var au2 = '</audio>';
    // ttsDiv.innerHTML = au1 + sss + eee + au2;
    //
    // ttsAudio = document.getElementById('tts_autio_id');
    //
    // ttsAudio.play();
    // }