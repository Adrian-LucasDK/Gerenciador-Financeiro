# Meu Financeiro — Gerenciador Financeiro em Rede Local

Sistema web em Python/Flask para controle financeiro pessoal com múltiplos usuários. Ele funciona em um computador servidor dentro da rede local (LAN). Os demais computadores acessam pelo navegador usando o endereço IP local do servidor.

> **Este projeto é somente para rede local.** Foram removidos os arquivos, dependências e instruções de hospedagem/publicação na internet. Não configure redirecionamento de portas no roteador.

## Funcionalidades

- Cadastro, login e logout de múltiplos usuários.
- Senhas armazenadas com hash seguro.
- Painel com receitas, despesas e saldo.
- Cadastro, edição e exclusão de lançamentos.
- Categorias, datas e observações.
- Cada usuário acessa somente seus próprios lançamentos.
- Administrador lista e exclui usuários.
- Excluir um usuário também apaga seus lançamentos.
- O administrador não pode excluir a própria conta nem o último administrador.
- Proteção CSRF nos formulários.
- Banco SQLite salvo localmente na pasta `instance/`.
- Interface e estilos armazenados localmente, sem CDN ou dependência de internet para carregar a página.

## Requisitos

- Windows 10/11 no computador que será o servidor.
- Python 3.10 ou superior (recomendado Python 3.12).
- Computadores conectados à mesma rede local (cabo ou Wi-Fi).

## 1. Preparar o projeto

Extraia o ZIP e abra a pasta `gerenciador_financeiro_rede_local` no VS Code.

No terminal PowerShell, dentro da pasta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, execute:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Instalar dependências

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Criar o primeiro administrador

## 3. Criar o primeiro administrador

O sistema cria automaticamente uma conta de administrador na primeira inicialização, caso ainda não exista nenhum administrador cadastrado.

**Credenciais padrão:**

| Campo | Valor |
|---|---|
| Nome | Administrador |
| E-mail | `admin@financeiro.com.br` |
| Senha | `Financeiro@2026` |
| Perfil | Administrador |

**Importante:** essas credenciais são destinadas ao primeiro acesso. Altere a senha após entrar no sistema e não compartilhe esses dados com outras pessoas.

Se desejar utilizar credenciais próprias, defina as variáveis de ambiente antes de iniciar o programa:

```powershell
$env:SECRET_KEY="coloque-uma-chave-aleatoria-longa"
$env:ADMIN_NAME="Administrador"
$env:ADMIN_EMAIL="admin@financeiro.com.br"
$env:ADMIN_PASSWORD="SuaSenhaForteAqui"
python app.py
```

O administrador será salvo no banco de dados `instance/financeiro.db`. Nas próximas inicializações, a conta existente será mantida.

**Acesso ao sistema:**

- E-mail: `admin@financeiro.com.br`
- Senha: `Financeiro@2026`

## 4. Iniciar o servidor local

No computador que ficará ligado como servidor, execute:

```powershell
python app.py
```

O Flask ficará ouvindo na porta `5000` em todas as interfaces de rede do computador. Mantenha o terminal aberto enquanto o sistema estiver em uso.

No próprio servidor, acesse:

```text
http://127.0.0.1:5000
```

## 5. Descobrir o IP do servidor

No computador servidor, abra outro PowerShell ou Prompt de Comando e execute:

```powershell
ipconfig
```

Localize o adaptador que está conectado à rede (Wi-Fi ou Ethernet) e procure **Endereço IPv4**. Exemplo: `192.168.1.50`.

Em outro computador conectado à mesma rede, abra o navegador e digite:

```text
http://192.168.1.50:5000
```

Troque `192.168.1.50` pelo IPv4 real do computador servidor.

Todos os usuários podem acessar o mesmo endereço, cada um entrando com sua própria conta.

## 6. Liberar no Firewall do Windows

Na primeira execução, o Windows pode perguntar se o Python pode se comunicar em redes. Permita somente em **redes privadas** (rede doméstica/organizacional confiável).

Se a janela não aparecer, abra o PowerShell como Administrador e execute:

```powershell
New-NetFirewallRule -DisplayName "Meu Financeiro - Rede Local" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Profile Private
```

Não crie regra para perfil público. Para remover a regra:

```powershell
Remove-NetFirewallRule -DisplayName "Meu Financeiro - Rede Local"
```

## 7. Recomendações para manter o acesso

- Reserve um IP para o computador servidor no roteador (reserva DHCP), para o endereço não mudar.
- Mantenha o computador servidor ligado e conectado à rede.
- Não feche o terminal enquanto o aplicativo estiver em uso.
- Não configure DMZ, encaminhamento de portas ou acesso externo no roteador.
- Use somente em uma rede local confiável; qualquer pessoa que consiga alcançar o servidor e tenha uma conta poderá entrar.
- Faça cópias de segurança do arquivo `instance/financeiro.db`.

## 8. Gerenciar o sistema

1. Entre com a conta administradora.
2. Cadastre novos usuários pelo link **Cadastre-se** na tela de login.
3. Em **Lançamentos**, registre receitas e despesas.
4. Em **Usuários**, o administrador pode excluir contas.
5. A exclusão de uma conta remove permanentemente os lançamentos associados.

## Estrutura do projeto

```text
gerenciador_financeiro_rede_local/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── instance/                 # Criada automaticamente
│   └── financeiro.db         # Banco local (não enviar)
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── transactions.html
│   ├── transaction_form.html
│   ├── users.html
│   └── error.html
└── static/
    └── style.css
```

## Tecnologias

Python • Flask • Flask-Login • Flask-SQLAlchemy • SQLite • Flask-WTF • HTML • CSS

## Observação importante

O servidor de desenvolvimento do Flask é utilizado aqui para uma aplicação interna de rede local e permanece com `debug=False`. Não exponha a porta 5000 à internet. Para uso em ambientes com dados sensíveis ou muitos acessos simultâneos, avalie uma infraestrutura interna dedicada, backups automatizados e uma revisão de segurança.
