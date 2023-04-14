/*---------------------------------
アバター選択フォーム用JS
 ---------------------------------*/

$(function(){

    // 最大ファイル容量
    const maxFileSize = 16 * 1024 * 1024
    // 最低画像サイズ
    const minImagePx = 100

    // jQueryオブジェクト
    const $avatarPreview = $('#avatar-preview');
    const $avatarPreviewImage = $("#avatar-preview img");
    const $selectAvatar = $('#select-avatar');
    const $fileError = $('#file-error');

    // 既存のアバターを変更する
    $('#show-form').click(function(){
        $('#existing-avatar').hide();
        $('#new-avatar').show();
    });

    // メインフォーム
    $selectAvatar.on('change', function (e) {

        // 初期化
        $avatarPreviewImage.removeAttr('width');
        $avatarPreviewImage.removeAttr('height');
        $(this).removeClass('is-invalid');
        $fileError.html('');

        // 画像が無いときはプレースホルダを表示
        if ($(this).val() == '') {

            $avatarPreview.addClass("avatar-placeholder")
            $avatarPreviewImage.attr('src', "");

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
                $avatarPreview.removeClass("avatar-placeholder");
                $avatarPreviewImage.attr('src', e.target.result);
            }
            
            let image = new Image();
            image.onload = function() {
                if (image.naturalWidth < minImagePx | image.naturalHeight < minImagePx) {
                    $avatarPreviewImage.attr('src', "");
                    $avatarPreview.addClass("avatar-placeholder")
                    $selectAvatar.val("");
                    $selectAvatar.addClass('is-invalid');
                    $fileError.html(`画像のサイズは縦横${minImagePx}px以上である必要があります。`)
                } else {
                    if (image.naturalWidth < image.naturalHeight) {
                        $avatarPreviewImage.attr('width', '100px');
                    } else {
                        $avatarPreviewImage.attr('height', '100px');
                    }
                }
            } 
            reader.readAsDataURL(e.target.files[0]);
        }
    });

});