import pytest
import asyncio
from app.core.botfather_orchestrator import botfather_orchestrator, _normalize_username, _extract_token, BotCreationState, BOTFATHER_ID


def test_normalize_username():
    assert _normalize_username("TestShop") == "TestShop_bot"
    assert _normalize_username("mybot") == "mybot"
    assert _normalize_username("weird name!*") == "weirdname_bot"


def test_extract_token():
    txt = "Use this token: 123456789:abcdefghijklmnopqrstuvwxyz_12345"
    tok = _extract_token(txt)
    assert tok and ":" in tok


@pytest.mark.asyncio
async def test_state_machine_transitions(monkeypatch):
    async def no_send(vendor_id, chat_id, text):
        await asyncio.sleep(0)
        return

    async def no_persist(self, vendor_id, st):
        await asyncio.sleep(0)
        return
    monkeypatch.setattr("app.core.botfather_orchestrator.mtproto_manager.send_message", no_send)
    monkeypatch.setattr("app.core.botfather_orchestrator.BotFatherOrchestrator._persist_state", no_persist)

    vendor_id = 9999
    try:
        await botfather_orchestrator.start_auto_create(vendor_id, "Mi Bot", "mi_tienda")
        st = botfather_orchestrator.get_state(vendor_id)
        assert st and st.status == "sent_newbot" and st.expected == "ask_name"

        await botfather_orchestrator.on_botfather_message(vendor_id, "Please choose a name for your bot", {})
        st = botfather_orchestrator.get_state(vendor_id)
        assert st and st.status == "sent_name" and st.expected == "ask_username"

        await botfather_orchestrator.on_botfather_message(vendor_id, "Now choose a username", {})
        st = botfather_orchestrator.get_state(vendor_id)
        assert st and st.status == "sent_username" and st.expected == "waiting_token"

        token_msg = "Done! Keep your token: 123456789:abcdefghijklmnopqrstuvwxyz_12345"
        await botfather_orchestrator.on_botfather_message(vendor_id, token_msg, {})
        st = botfather_orchestrator.get_state(vendor_id)
        assert st and st.status == "completed" and st.token is not None
    finally:
        botfather_orchestrator._states.pop(vendor_id, None)
