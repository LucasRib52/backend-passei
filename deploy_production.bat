@echo off
setlocal enabledelayedexpansion

REM Script de Deploy para Produção com Sincronização Automática (Windows)
REM Use este script quando fizer deploy para produção

set PROJECT_DIR=%~dp0
set LOG_FILE=%PROJECT_DIR%deploy.log
set PYTHON_PATH=python

echo [%date% %time%] 🚀 Iniciando deploy para produção... >> "%LOG_FILE%"
echo 🚀 Iniciando deploy para produção...
echo Diretório: %PROJECT_DIR%

REM PASSO 1: Verificar ambiente
echo [%date% %time%] 🔍 Verificando ambiente... >> "%LOG_FILE%"
echo 🔍 Verificando ambiente...

if exist ".env" (
    echo ✅ Arquivo .env encontrado
    echo [%date% %time%] ✅ Arquivo .env encontrado >> "%LOG_FILE%"
) else (
    echo ⚠️ Arquivo .env não encontrado - usando variáveis do sistema
    echo [%date% %time%] ⚠️ Arquivo .env não encontrado >> "%LOG_FILE%"
)

REM PASSO 2: Ativar ambiente virtual (se existir)
if exist "venv\Scripts\activate.bat" (
    echo 🐍 Ativando ambiente virtual...
    echo [%date% %time%] 🐍 Ativando ambiente virtual... >> "%LOG_FILE%"
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo [%date% %time%] ✅ Ambiente virtual ativado >> "%LOG_FILE%"
) else if exist ".venv\Scripts\activate.bat" (
    echo 🐍 Ativando ambiente virtual (.venv)...
    echo [%date% %time%] 🐍 Ativando ambiente virtual (.venv)... >> "%LOG_FILE%"
    call .venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
    echo [%date% %time%] ✅ Ambiente virtual ativado >> "%LOG_FILE%"
) else (
    echo ⚠️ Nenhum ambiente virtual encontrado
    echo [%date% %time%] ⚠️ Nenhum ambiente virtual encontrado >> "%LOG_FILE%"
)

REM PASSO 3: Instalar/atualizar dependências
echo 📦 Verificando dependências...
echo [%date% %time%] 📦 Verificando dependências... >> "%LOG_FILE%"

if exist "requirements.txt" (
    %PYTHON_PATH% -m pip install -r requirements.txt --quiet
    echo ✅ Dependências atualizadas
    echo [%date% %time%] ✅ Dependências atualizadas >> "%LOG_FILE%"
) else (
    echo ⚠️ requirements.txt não encontrado
    echo [%date% %time%] ⚠️ requirements.txt não encontrado >> "%LOG_FILE%"
)

REM PASSO 4: Executar deploy com sincronização
echo 🔄 Executando deploy com sincronização automática...
echo [%date% %time%] 🔄 Executando deploy com sincronização automática... >> "%LOG_FILE%"

%PYTHON_PATH% manage.py deploy_with_sync --force

REM PASSO 5: Verificar se tudo funcionou
echo 🔍 Verificando resultado do deploy...
echo [%date% %time%] 🔍 Verificando resultado do deploy... >> "%LOG_FILE%"

%PYTHON_PATH% manage.py check --deploy >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Verificação de deploy passou
    echo [%date% %time%] ✅ Verificação de deploy passou >> "%LOG_FILE%"
) else (
    echo ❌ Verificação de deploy falhou
    echo [%date% %time%] ❌ Verificação de deploy falhou >> "%LOG_FILE%"
    exit /b 1
)

REM Verificar produtos sincronizados
for /f "tokens=*" %%i in ('%PYTHON_PATH% manage.py shell -c "from themembers.models import TheMembersProduct; print(TheMembersProduct.objects.count())" 2^>nul') do set PRODUCT_COUNT=%%i

if !PRODUCT_COUNT! gtr 0 (
    echo ✅ Produtos TheMembers sincronizados: !PRODUCT_COUNT!
    echo [%date% %time%] ✅ Produtos TheMembers sincronizados: !PRODUCT_COUNT! >> "%LOG_FILE%"
) else (
    echo ⚠️ Nenhum produto TheMembers encontrado
    echo [%date% %time%] ⚠️ Nenhum produto TheMembers encontrado >> "%LOG_FILE%"
)

REM Resumo final
echo 🎉 Deploy concluído com sucesso!
echo [%date% %time%] 🎉 Deploy concluído com sucesso! >> "%LOG_FILE%"
echo 📊 Resumo:
echo [%date% %time%] 📊 Resumo: >> "%LOG_FILE%"
echo    • Produtos TheMembers: !PRODUCT_COUNT!
echo [%date% %time%]    • Produtos TheMembers: !PRODUCT_COUNT! >> "%LOG_FILE%"
echo    • Log salvo em: %LOG_FILE%
echo [%date% %time%]    • Log salvo em: %LOG_FILE% >> "%LOG_FILE%"
echo    • Data/Hora: %date% %time%
echo [%date% %time%]    • Data/Hora: %date% %time% >> "%LOG_FILE%"

echo.
echo 📋 PRÓXIMOS PASSOS:
echo 1. Reinicie o servidor web na PythonAnywhere
echo 2. Teste a API: curl https://seu-dominio.com/api/v1/themembers/products/
echo 3. Verifique os logs em: %LOG_FILE%
echo 4. Monitore a aplicação por alguns minutos
echo.

echo ✅ Deploy finalizado! 🚀
echo [%date% %time%] ✅ Deploy finalizado! 🚀 >> "%LOG_FILE%"

pause
