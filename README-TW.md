# Pubu PoC

[English version](README.md)

這份程式碼實作了公開於HITCON ZeroDay的[ZD-2023-00144](https://zeroday.hitcon.org/vulnerability/ZD-2023-00144)漏洞。攻擊者可以利用這個漏洞在沒有購買的狀態下將[pubu.com.tw](https://www.pubu.com.tw/)網站上的電子書下載下來。
關於這個漏洞的更多資訊，請參考[這篇部落格文章](https://joeywang.tw/zh-TW/blog/pubu-vulnerability/)。

**注意⚠️**: 這份程式碼只是用來證明漏洞的可行性，僅限於學術用途。下載具有版權的檔案可能會觸犯法律以及網站規範，**使用前請三思**。

**更新 (2023/08/27)**：目前這個漏洞已被修補。

## Demo

[![Watch the video](https://img.youtube.com/vi/f496UUln1z0/0.jpg)](https://youtu.be/f496UUln1z0)

## 使用方法

這份程式碼需要`python3` (版本 >= 3.8)以及一些額外套件。

1. 下載程式碼：`git clone https://github.com/joeywang4/Pubu-PoC`
2. 切換至程式碼資料夾：`cd Pubu-PoC`
3. 安裝額外套件：`pip install -r requirements.txt`
4. 開始下載電子書：`python main.py -v [book_id ...]`
5. 下載好的電子書會存放於`output/`資料夾中。

下載電子書時會需要用到`book_id`，這是電子書的編號，可以在電子書的網址中找到。
舉例來說，`https://www.pubu.com.tw/ebook/999`這個網址為編號999的電子書網址，而下載此書時需執行`python main.py -v 999`。

### 執行參數

在執行`main.py`時可以提供一些額外參數來改變執行模式以及下載資料夾。以下將列出一些主要參數，完整列表可以執行`python main.py -h`查看。

- `-v` 或 `--verbose`：執行時顯示更多資訊
- `-t` 或 `--threads`：調整爬蟲的執行緒數量
- `-o` 或 `--output`：設定下載資料夾(預設為`output/`)
- `-c` 或 `--change-decode`：調整產生PDF文件時的解碼模式。當電子書檔案發生錯誤時可以使用這個參數。

### 已知問題

1. 解碼錯誤：有時電子書在進行解碼時會發生問題，導致書本頁面排列有誤，此時可以重新下載書籍並使用`-c`參數進行修正。
2. 卡在搜尋步驟：有些電子書的書頁排列不連續導致搜尋需花費相當長的時間才能完成。若遇到此狀況請耐心等候或在下載前先[預載離線資料庫](#%E9%9B%A2%E7%B7%9A%E8%B3%87%E6%96%99%E5%BA%AB)(也需花費許多時間)。

## 離線資料庫

在下載書籍時需要搜尋書頁資料，而這個步驟有時需等待很久。這份程式碼也提供了預先下載離線資料庫的功能，在下載電子書時即可跳過搜尋的步驟。

若是想要先預載離線資料庫，可以執行`python main.py -u pages`來預載書頁資料，或是使用`-u all`參數將書籍資料一併下載至離線資料庫中。關於離線資料庫的更多資訊，請參考[這份文件](database.md)(僅限英文)。 

注意：預載離線資料庫需花費數天，而這些資料將會占用約1G的空間。

## 測試

可以執行`pytest`來執行`test/`中的測試程式碼。

## 改進程式碼

歡迎發送PR來對程式碼進行修改!
修改程式碼之後請執行[black](https://github.com/psf/black)與[pylint](https://www.pylint.org/)，可能的話也請新增測試程式碼。
