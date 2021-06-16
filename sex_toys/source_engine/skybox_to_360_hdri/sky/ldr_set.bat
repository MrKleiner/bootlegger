@echo off
REM setlocal
REM :PROMPT
REM SET /P AREYOUSURE=Also convert input vtfs to tgas (Y/[N])?
REM IF /I "%AREYOUSURE%" NEQ "N" GOTO SRENAME
REM IF /I "%AREYOUSURE%" NEQ "Y" GOTO CONVTGA

CHOICE /C YS /M "Also convert input vtfs to tgas (Y/[N])"
IF %ERRORLEVEL% EQU 2 goto SRENAME
IF %ERRORLEVEL% EQU 1 goto CONVTGA

echo ... end ...


:SRENAME

ren *bk.* sky_bk.*
ren *dn.* sky_dn.*
ren *ft.* sky_ft.*
ren *lf.* sky_lf.*
ren *rt.* sky_rt.*
ren *up.* sky_up.*



:CONVTGA
set /P v2tdir=Specify vtf2tga dir NO SLASH IN THE END: 

del /F /Q %~dp0\vtf_src\ldr\*
del /F /Q %~dp0\vtf_src\temp\*

REM xcopy %~dp0*pootis.* %~dp0\vtf_src\ldr

xcopy %~dp0*bk.vtf %~dp0\vtf_src\temp
xcopy %~dp0*dn.vtf %~dp0\vtf_src\temp
xcopy %~dp0*ft.vtf %~dp0\vtf_src\temp
xcopy %~dp0*lf.vtf %~dp0\vtf_src\temp
xcopy %~dp0*rt.vtf %~dp0\vtf_src\temp
xcopy %~dp0*up.vtf %~dp0\vtf_src\temp

move %~dp0*bk.vtf %~dp0\vtf_src\ldr
move %~dp0*dn.vtf %~dp0\vtf_src\ldr
move %~dp0*ft.vtf %~dp0\vtf_src\ldr
move %~dp0*lf.vtf %~dp0\vtf_src\ldr
move %~dp0*rt.vtf %~dp0\vtf_src\ldr
move %~dp0*up.vtf %~dp0\vtf_src\ldr

ren %~dp0\vtf_src\temp\*bk.* sky_bk.vtf
ren %~dp0\vtf_src\temp\*dn.* sky_dn.vtf
ren %~dp0\vtf_src\temp\*ft.* sky_ft.vtf
ren %~dp0\vtf_src\temp\*lf.* sky_lf.vtf
ren %~dp0\vtf_src\temp\*rt.* sky_rt.vtf
ren %~dp0\vtf_src\temp\*up.* sky_up.vtf

"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_bk.vtf -o %~dp0result_tga\sky_bk
"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_dn.vtf -o %~dp0result_tga\sky_dn
"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_ft.vtf -o %~dp0result_tga\sky_ft
"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_lf.vtf -o %~dp0result_tga\sky_lf
"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_rt.vtf -o %~dp0result_tga\sky_rt
"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_up.vtf -o %~dp0result_tga\sky_up

REM ren *bk.vtf sky_bk_vsrc.vtf
REM ren *dn.vtf sky_dn_vsrc.vtf
REM ren *ft.vtf sky_ft_vsrc.vtf
REM ren *lf.vtf sky_lf_vsrc.vtf
REM ren *rt.vtf sky_rt_vsrc.vtf
REM ren *up.vtf sky_up_vsrc.vtf

REM %v2tdir%\vtf2tga.exe -i 

del /F /Q %~dp0\vtf_src\temp\*

REM endlocal