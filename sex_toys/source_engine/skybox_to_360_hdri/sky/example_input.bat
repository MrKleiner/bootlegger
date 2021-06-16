REM "E:\Gamess\steamapps\common\Half-Life 2\bin\vtf2tga.exe" -i %~dp0\dev_test\super_sky.vtf -o %~dp0\converted_shit
REM del /F /Q %~dp0\vtf_src\ldr\*
REM xcopy %~dp0*pootis.* %~dp0\dev_test

REM move %~dp0*pootis.txt %~dp0\dev_test
REM %v2tdir%\vtf2tga.exe -i %~dp0\vtf_src\ldr\*bk.vtf -o %~dp0\sky_bk
REM "E:\Gamess\steamapps\common\Half-Life 2\bin\vtf2tga.exe" -i %~dp0vtf_src\ldr\*bk.vtf -o %~dp0sky_bk

ren %~dp0\vtf_src\temp\*bk.* sky_bk.vtf