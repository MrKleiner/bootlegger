@echo off

CHOICE /C YN /M "16bit HDR? (Y/[N])"
IF %ERRORLEVEL% EQU 2 goto ELDR
IF %ERRORLEVEL% EQU 1 goto SBITHDR

:ELDR

del /F /Q %~dp0\vtf_src\ldr\*
del /F /Q %~dp0\vtf_src\temp\*

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



"%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_bk.vtf -o %~dp0result_tga\sky_bk
"%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_dn.vtf -o %~dp0result_tga\sky_dn
"%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_ft.vtf -o %~dp0result_tga\sky_ft
"%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_lf.vtf -o %~dp0result_tga\sky_lf
"%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_rt.vtf -o %~dp0result_tga\sky_rt
"%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe" -i %~dp0vtf_src\temp\sky_up.vtf -o %~dp0result_tga\sky_up

del /F /Q %~dp0\vtf_src\temp\*

EXIT


:SBITHDR

del /F /Q %~dp0\vtf_src\hdr\*
del /F /Q %~dp0\vtf_src\temp\*
del /F /Q %~dp0\vtf_src\pfm_decomp\*


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

%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe -i %~dp0vtf_src\temp\sky_bk.vtf -o %~dp0vtf_src\pfm_decomp\sky_bk
%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe -i %~dp0vtf_src\temp\sky_dn.vtf -o %~dp0vtf_src\pfm_decomp\sky_dn
%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe -i %~dp0vtf_src\temp\sky_ft.vtf -o %~dp0vtf_src\pfm_decomp\sky_ft
%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe -i %~dp0vtf_src\temp\sky_lf.vtf -o %~dp0vtf_src\pfm_decomp\sky_lf
%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe -i %~dp0vtf_src\temp\sky_rt.vtf -o %~dp0vtf_src\pfm_decomp\sky_rt
%~dp0\vtf_src\util\vtf2tga\vtf2tga.exe -i %~dp0vtf_src\temp\sky_up.vtf -o %~dp0vtf_src\pfm_decomp\sky_up

%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_bk.pfm %~dp0result_exr\sky_bk.exr
%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_dn.pfm %~dp0result_exr\sky_dn.exr
%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_ft.pfm %~dp0result_exr\sky_ft.exr
%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_lf.pfm %~dp0result_exr\sky_lf.exr
%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_rt.pfm %~dp0result_exr\sky_rt.exr
%~dp0vtf_src\util\pfm2exr\magick.exe %~dp0vtf_src\pfm_decomp\sky_up.pfm %~dp0result_exr\sky_up.exr

del /F /Q %~dp0\vtf_src\temp\*
EXIT
