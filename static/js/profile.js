/*---------------------------------
　プロフィール変更画面用JS
 ---------------------------------*/

$(function(){

  /*
  カウント関数
  ————————————————————*/
  let count = function(target, display, maxLength) {
    // 入力中の文字数を表示
    let currentLength = $(target).val().length;
    $(display).text(`（${currentLength}文字/${maxLength}文字）`);
    // 最大文字数を超えたら赤文字にする
    if (maxLength < currentLength) {
      $(display).addClass('bs-danger-text');
    } else {
      $(display).removeClass('bs-danger-text');
    }
  }
  
  /*
  自己紹介文字数カウント
  ————————————————————*/
  const $profileTarget = $('#profile-textarea');
  const $profileDisplay = $('#profile-count');
  const profileMaxLength = 100;  // 最大文字数

  count($profileTarget, $profileDisplay, profileMaxLength);
  $profileTarget.keyup(function(){
    count($profileTarget, $profileDisplay, profileMaxLength);
  });

});