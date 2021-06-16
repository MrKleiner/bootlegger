@echo off
REM set /P v2tdir=Specify vtf2tga dir NO SLASH IN THE END: 

REM del *.tga
REM del %~dp0\dev_test\*.tga
REM %v2tdir%\vtf2tga.exe -i 
REM echo %v2tdir%\vtf2tga.exe

REM @echo off
REM setlocal
REM :PROMPT
REM SET /P AREYOUSURE=Also convert input vtfs to tgas (Y/[N])?
REM IF /I "%AREYOUSURE%" NEQ "N" GOTO SRENAME
REM IF /I "%AREYOUSURE%" NEQ "Y" GOTO CONVTGA

REM CHOICE /C YS /M "Also convert input vtfs to tgas (Y/[N])"
REM IF %ERRORLEVEL% EQU 2 goto SRENAME
REM IF %ERRORLEVEL% EQU 1 goto CONVTGA

REM echo ... end ...


REM :SRENAME

REM ren *bk.* sky_bk.*
REM ren *dn.* sky_dn.*
REM ren *ft.* sky_ft.*
REM ren *lf.* sky_lf.*
REM ren *rt.* sky_rt.*
REM ren *up.* sky_up.*



REM :CONVTGA
set /P v2tdir=Specify vtf2tga dir NO SLASH IN THE END: 

del /F /Q %~dp0\vtf_src\hdr\*
del /F /Q %~dp0\vtf_src\temp\*
del /F /Q %~dp0\vtf_src\pfm_decomp\*

REM xcopy %~dp0*pootis.* %~dp0\vtf_src\ldr

xcopy %~dp0*bk.vtf %~dp0\vtf_src\temp
xcopy %~dp0*dn.vtf %~dp0\vtf_src\temp
xcopy %~dp0*ft.vtf %~dp0\vtf_src\temp
xcopy %~dp0*lf.vtf %~dp0\vtf_src\temp
xcopy %~dp0*rt.vtf %~dp0\vtf_src\temp
xcopy %~dp0*up.vtf %~dp0\vtf_src\temp

move %~dp0*bk.vtf %~dp0\vtf_src\hdr
move %~dp0*dn.vtf %~dp0\vtf_src\hdr
move %~dp0*ft.vtf %~dp0\vtf_src\hdr
move %~dp0*lf.vtf %~dp0\vtf_src\hdr
move %~dp0*rt.vtf %~dp0\vtf_src\hdr
move %~dp0*up.vtf %~dp0\vtf_src\hdr

ren %~dp0\vtf_src\temp\*bk.* sky_bk.vtf
ren %~dp0\vtf_src\temp\*dn.* sky_dn.vtf
ren %~dp0\vtf_src\temp\*ft.* sky_ft.vtf
ren %~dp0\vtf_src\temp\*lf.* sky_lf.vtf
ren %~dp0\vtf_src\temp\*rt.* sky_rt.vtf
ren %~dp0\vtf_src\temp\*up.* sky_up.vtf

"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_bk.vtf -o %~dp0vtf_src\pfm_decomp\sky_bk
"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_dn.vtf -o %~dp0vtf_src\pfm_decomp\sky_dn
"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_ft.vtf -o %~dp0vtf_src\pfm_decomp\sky_ft
"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_lf.vtf -o %~dp0vtf_src\pfm_decomp\sky_lf
"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_rt.vtf -o %~dp0vtf_src\pfm_decomp\sky_rt
"%v2tdir%\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_up.vtf -o %~dp0vtf_src\pfm_decomp\sky_up

%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_bk.pfm %~dp0result_exr\sky_bk.exr
%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_dn.pfm %~dp0result_exr\sky_dn.exr
%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_ft.pfm %~dp0result_exr\sky_ft.exr
%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_lf.pfm %~dp0result_exr\sky_lf.exr
%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_rt.pfm %~dp0result_exr\sky_rt.exr
%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_up.pfm %~dp0result_exr\sky_up.exr

REM ren *bk.vtf sky_bk_vsrc.vtf
REM ren *dn.vtf sky_dn_vsrc.vtf
REM ren *ft.vtf sky_ft_vsrc.vtf
REM ren *lf.vtf sky_lf_vsrc.vtf
REM ren *rt.vtf sky_rt_vsrc.vtf
REM ren *up.vtf sky_up_vsrc.vtf

REM %v2tdir%\vtf2tga.exe -i 

del /F /Q %~dp0\vtf_src\temp\*

REM endlocal