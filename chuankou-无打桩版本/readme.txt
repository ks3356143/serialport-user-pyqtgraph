打包方法：
1.打包带控制台的可执行程序，在dict里，但是注意可执行程序要和图片image文件夹一起
    Pyinstaller -F main.py
2.不带控制台
    Pyinstaller -F -w main.py
3.使用资源文件.qrc打包
    Pyinstaller -o re_rc.py re.qrc
4.打包增加图标
    Pyinstaller -F -w main.py -i 图标绝对路径

5.
pyinstaller --hidden-import=pkg_resources -F main.py
6.
pyinstaller38 --hidden-import=pkg_resources -F -w -i m4.ico main.py


pyinstaller -D --noconsole --hidden-import="axisCtrlTemplate_pyqt5"  main.py
