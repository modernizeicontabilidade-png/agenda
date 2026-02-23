# AgendaAvisos

Aplicativo desktop para **Windows 10/11** de agenda e lembretes offline, com popup no horário exato.

## 1) Arquitetura e stack escolhida

### Stack escolhida
**Python + PySide6 + APScheduler + SQLite**.

### Justificativa (curta)
- **Menor atrito para rodar/empacotar no Windows** com `PyInstaller`.
- **PySide6** entrega componentes nativos para UI, incluindo **Date Picker com calendário visual** (`QDateEdit` + `calendarPopup=True`) e seletor de hora (`QTimeEdit`).
- **APScheduler** facilita agendamento em background no processo.
- **SQLite** garante persistência local, simples e offline.

### Estrutura de pastas

```text
agenda_avisos/
  core/
    models.py
    reminder_logic.py
    startup.py
  db/
    database.py
  scheduler/
    reminder_scheduler.py
  ui/
    main_window.py
    reminder_dialog.py
    popup_dialog.py
  utils/
    logging_config.py
main.py
requirements.txt
```

## 2) Funcionalidades implementadas

- CRUD de lembretes (criar/listar/editar/excluir).
- Campos: título, mensagem, data, hora, repetição (Nenhuma/Diária/Semanal/Mensal).
- Validação de data/hora futura.
- Persistência local em SQLite.
- Reagendamento automático ao iniciar.
- Detecção de lembretes vencidos ao abrir e popup de “Atrasado”.
- Popup com botões:
  - OK
  - Soneca (5 min)
  - Soneca (15 min)
  - Adiar para amanhã
  - Marcar como concluído
- Opção “Iniciar com Windows” (registro `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).
- Logs em arquivo local `logs/agenda_avisos.log`.

## 3) Como instalar dependências

> Requisito: Python 3.11+ no Windows.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4) Como rodar

```bash
.venv\Scripts\activate
python main.py
```

## 5) Como gerar executável (.exe)

### Instalar empacotador

```bash
pip install pyinstaller
```

### Gerar executável

```bash
pyinstaller --noconfirm --windowed --name AgendaAvisos main.py
```

Saída principal:
- `dist\AgendaAvisos\AgendaAvisos.exe`

## 6) Iniciar com Windows

No app, marque o checkbox **“Iniciar com Windows”**.

Internamente, o app escreve/remove a chave no Registro do usuário atual:

- `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- Nome da entrada: `AgendaAvisos`

## 7) Banco de dados

Arquivo padrão:
- `data/agenda_avisos.db`

Tabelas:
- `reminders`
- `settings`

## 8) Checklist de testes manuais

1. **Criar lembrete único futuro** e confirmar que aparece na lista.
2. **Selecionar data via calendário visual** no formulário de criação.
3. **Selecionar hora via campo de hora**.
4. Tentar criar com data/hora passada e validar bloqueio.
5. Aguardar disparo e testar popup com **OK**.
6. Criar lembrete e testar **Soneca 5 min**.
7. Testar **Soneca 15 min**.
8. Testar **Adiar para amanhã**.
9. Testar **Marcar como concluído** e verificar status.
10. Criar lembrete **Diário** e verificar próxima ocorrência após disparar.
11. Criar lembrete **Semanal** e verificar próxima ocorrência.
12. Criar lembrete **Mensal** e verificar próxima ocorrência.
13. Fechar e abrir app: confirmar que lembretes ativos são recarregados.
14. Simular lembrete vencido (hora passada com app fechado) e confirmar popup “Atrasado” ao abrir.
15. Marcar/desmarcar “Iniciar com Windows” e validar chave no Registro.

## 9) Observações

- O app foi desenhado para operação offline.
- Não usa serviços externos.
- Em ambientes não-Windows, o toggle de startup não terá efeito no Registro.
