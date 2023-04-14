/*---------------------------------
　会員登録画面用JS
 ---------------------------------*/

$(function(){

    /*
    規約同意にチェックが入ると確認ボタンが有効になる
    ————————————————————————————————————————————*/
    $("#terms-check").change(function(){
        if ($("#terms-check").prop("checked")) {
            $("#signup-btn").prop("disabled", false)
        } else {
            $("#signup-btn").prop("disabled", true)
        }
    });

});