/*---------------------------------
　パスワード設定フォーム用JS
 ---------------------------------*/

$(function(){

    /*
    パスワード強度チェッカー
    ————————————————————————————————————————————*/
    $("#input-password").pwdMeasure({
        minScore: 50,
        minLength: 6,
        events: "keyup change",
        labels: [
          {score:10,         label:"とても弱い", className:"very-weak"},   //0~10%
          {score:30,         label:"弱い",       className:"weak"},        //11~30%
          {score:50,         label:"平均",       className:"average"},     //31~50%
          {score:70,         label:"強い",       className:"strong"},      //51~70%
          {score:100,        label:"とても強い", className:"very-strong"}, //71~100%
          {score:"notMatch", label:"不一致",     className:"not-match"},   //not match
          {score:"empty",    label:"未入力",     className:"empty"}        //empty
        ], 
        indicator: "#pm-indicator",
        indicatorTemplate: '<span id="pm-bar"></span><span id="pm-label"><%= label %> (<%= percentage %>%)</span>',
        confirm: false,
      
        // Callbacks
        onValid: false,
        onInvalid: false,
        onNotMatch: false,
        onEmpty: false,
        onChangeState: false,
        onChangeValue: false
    });

});