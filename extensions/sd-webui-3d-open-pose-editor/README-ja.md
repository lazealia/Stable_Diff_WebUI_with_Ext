# 3D Openpose Editor (sd-webui-3d-open-pose-editor) [[English](README.md)] [[中文版](README-zh.md)]

[Online 3D Openpose Editor](https://github.com/ZhUyU1997/open-pose-editor)を[stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui)で使うための拡張機能です。

# プレビュー

![Preview](https://user-images.githubusercontent.com/42905588/227674599-21610711-7276-413c-aa36-cc5108e74dc3.png)

# インストール

1. WebUIの「Extension」タブを開きます
2. 「Available」タブを開きます
3. WebUIが古い場合は「Extension index URL」を `https://raw.githubusercontent.com/AUTOMATIC1111/stable-diffusion-webui-extensions/master/index.json` に変更してください
4. 「Load from:」ボタンをクリックします
5. 3D Openpose Editorの「Install」ボタンをクリックします
6. 「Installed」タブを開き、「Apply and restart UI」ボタンをクリックします

# 特徴

- **ポーズの編集**: マウスで関節を選択し、回転させることで、3Dモデルのポーズを編集できます。

- **手の編集**: 手のボーンを選択し、色付きの円を調整することで、手の位置を微調整できます。

- **深度/法線/Cannyマップ**: 深度、法線、Cannyマップを生成して可視化することで、AIの描画力を向上させることができます。

- **シーンの保存/読み込み/復元**: シーンの保存・読み込み機能が備わっているため、作成中のシーンを保存して後で復元できます。

- **身体パラメータの調整**: 高さ、幅、脚の長さなどの身体パラメータを調整して、カスタム3Dモデルを作成できます。
# 使い方
### カメラのナビゲーション:
- **カメラの回転**: 空いている場所を左クリックしながらマウスを移動します。
- **カメラの移動**: 空いている場所を右クリックしながらマウスを移動します。

### スケルトンの操作:
- **関節の回転**: 関節を左クリックで選択してから、色付きの円のうちの1つを押しながらマウスを移動します。
- **手の編集**: 赤い点をクリックして手のボーンを選択し、色付きの円のうちの1つを押しながらマウスを移動します。
### 身体パラメータの調整:
- **スケルトンの選択**: スケルトンをクリックして選択します。
- **身体パラメータを開く**: メニューの「身体パラメータ」をクリックして、パラメータを調整します。
### 出力解像度の調整:
- **メニューで出力解像度を調整**: メニューの「幅」または「高さ」を変更して、出力解像度を調整します。
### その他の機能:
- **移動モードに切り替え**: Xキーを押すと、移動モードに切り替わり、身体全体を移動できます。
- **ボディの削除**: Dキーを押して、身体全体を削除できます。

# 謝辞

* [ZhUyU1997 - Online 3D Openpose Editor](https://github.com/ZhUyU1997/open-pose-editor): オリジナル版
