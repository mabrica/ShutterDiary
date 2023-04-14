/*---------------------------------
　記事投稿・編集画面用JS
 ---------------------------------*/

$(function(){

    /*
    ファイルサイズチェック & 画像プレビュー
    ————————————————————————————————————*/

    // 最大ファイル容量
    const maxFileSize = 16 * 1024 * 1024
    // 最低画像サイズ
    const minImageWidth = 480
    const minImageHeight = 360

    // jQueryオブジェクト
    const $imagePreview = $('#image-preview');
    const $imagePreviewImage = $("#image-preview img");
    const $selectImage = $('#select-image');
    const $fileError = $('#file-error');

    $selectImage.on('change', function (e) {

        // 初期化
        $imagePreviewImage.removeAttr('width');
        $imagePreviewImage.removeAttr('height');
        $(this).removeClass('is-invalid');
        $fileError.html('');

        // 画像が無いときはプレースホルダを表示
        if ($(this).val() == '') {

            $imagePreview.addClass("image-placeholder")
            $imagePreviewImage.attr('src', "");

        // 画像があるときは画像をチェックして表示
        } else {

            // ファイルサイズチェック
            if (maxFileSize < $(this).prop('files')[0].size) {
                $(this).val("");
                $(this).addClass('is-invalid');
                $fileError.html('アップロードできる最大容量（16MB）を超えています。')
            }

            // プレビュー表示
            let reader = new FileReader();
            reader.onload = function (e) {
                image.src = reader.result;
                $imagePreview.removeClass("image-placeholder");
                $imagePreviewImage.attr('src', e.target.result);
            }

            let image = new Image();
            image.onload = function() {
                if (image.naturalWidth < minImageWidth | image.naturalHeight < minImageHeight) {
                    $imagePreviewImage.attr('src', "");
                    $imagePreview.addClass("image-placeholder")
                    $selectImage.val("");
                    $selectImage.addClass('is-invalid');
                    $fileError.html(`画像のサイズは横${minImageWidth}px、縦${minImageHeight}px以上である必要があります。`)
                }
            }
            reader.readAsDataURL(e.target.files[0]);
        }
    });


    /*
    カウント関数
    ————————————*/
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
    タイトル文字数カウント
    ————————————————————*/
    const $titleTarget = $('#input-title');
    const $titleDisplay = $('#title-count');
    const titleMaxLength = 50; // 最大文字数

    count($titleTarget, $titleDisplay, titleMaxLength);
    $titleTarget.keyup(function(){
        count($titleTarget, $titleDisplay, titleMaxLength);
    });


    /*
    本文文字数カウント
    —————————————————*/
    const $bodyTarget = $('#body-textarea');
    const $bodyDisplay = $('#body-count');
    const bodyMaxLength = 500;  // 最大文字数

    count($bodyTarget, $bodyDisplay, bodyMaxLength);
    $bodyTarget.keyup(function(){
        count($bodyTarget, $bodyDisplay, bodyMaxLength);
    });


    /*
    プライベートモードの切替ボタン
    ————————————————————————————*/

    const privateModeOn = "<span>ON</span><small>（投稿ユーザーのみ閲覧可能）</small>"
    const privateModeOff = "<span>OFF</span><small>（すべてのユーザーが閲覧可能）</small>"

    $("#is-private").change(function(){
        if ($("#is-private").prop("checked")) {
            $("#private-mode-state").addClass("is_on");
            $("#private-mode-state").html(privateModeOn);
        } else {
            $("#private-mode-state").removeClass("is_on");
            $("#private-mode-state").html(privateModeOff);
        }
    });


    /*
    既存の画像を変更するボタン
    ————————————————————————————*/
    $('#show-form').click(function(){
        $selectImage.val("");
        $imagePreviewImage.attr('src', "");
        $imagePreview.addClass("image-placeholder");
        $('#existing-image').hide();
        $('#image-form').show();
    });

    /*
    記事を削除するボタン
    ————————————————————————————*/
    $('#delete-post').click(function(){
        $('#form-wrapper').hide()
        $('#delete-confirm').show()
    });
    $('#cancel-delete').click(function(){
        $('#delete-confirm').hide()
        $('#form-wrapper').show()
    });
});