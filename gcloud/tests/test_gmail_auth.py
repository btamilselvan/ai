from unittest.mock import MagicMock

from gmail import auth as gmail_auth


def _fake_full_message(message_id: str) -> dict:
    return {
        "id": message_id,
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": "Hello"},
                {"name": "From", "value": "sender@example.com"},
                {"name": "Date", "value": "Mon, 3 Aug 2026 00:00:00 +0000"},
            ],
            "body": {"data": "aGVsbG8gd29ybGQ="},  # "hello world"
        },
    }


def _build_fake_service(history_response: dict, message_id: str):
    messages_resource = MagicMock()
    messages_resource.get.return_value.execute.return_value = _fake_full_message(message_id)

    history_resource = MagicMock()
    history_resource.list.return_value.execute.return_value = history_response

    users_resource = MagicMock()
    users_resource.history.return_value = history_resource
    users_resource.messages.return_value = messages_resource

    service = MagicMock()
    service.users.return_value = users_resource
    return service, history_resource, messages_resource


def test_fetch_mails_scopes_history_query_and_returns_added_messages(monkeypatch):
    monkeypatch.setattr(gmail_auth, "get_credentials", MagicMock())
    # No persisted checkpoint yet -> falls back to the notification's historyId.
    monkeypatch.setattr(gmail_auth, "_get_last_history_id", MagicMock(return_value=None))
    set_checkpoint_mock = MagicMock()
    monkeypatch.setattr(gmail_auth, "_set_last_history_id", set_checkpoint_mock)
    history_response = {
        "history": [
            # A real messagesAdded entry from the history API never carries
            # labelIds on the embedded message stub -- this must not matter.
            {"messagesAdded": [{"message": {"id": "msg1", "threadId": "t1"}}]},
            {"messagesDeleted": [{"message": {"id": "msg2", "threadId": "t2"}}]},
        ],
        "historyId": "150",
    }
    service, history_resource, messages_resource = _build_fake_service(history_response, "msg1")
    monkeypatch.setattr(gmail_auth, "build", MagicMock(return_value=service))

    result = gmail_auth.fetch_mails("100")

    history_resource.list.assert_called_once_with(
        userId="me", startHistoryId="100", labelId="INBOX", historyTypes=["messageAdded"]
    )
    assert len(result) == 1
    assert result[0].message_id == "msg1"
    assert result[0].sender == "sender@example.com"
    assert result[0].subject == "Hello"
    # Checkpoint advances to the mailbox's historyId as of this call, not the
    # notification's historyId that was passed in.
    set_checkpoint_mock.assert_called_once_with("150")


def test_fetch_mails_uses_persisted_checkpoint_over_notification_history_id(monkeypatch):
    # This is the bug this test guards against: history.list only returns
    # records *after* startHistoryId, so passing the notification's own
    # historyId (which represents the mailbox's current state) always comes
    # back empty. fetch_mails must prefer our persisted checkpoint instead.
    monkeypatch.setattr(gmail_auth, "get_credentials", MagicMock())
    monkeypatch.setattr(gmail_auth, "_get_last_history_id", MagicMock(return_value="90"))
    monkeypatch.setattr(gmail_auth, "_set_last_history_id", MagicMock())
    history_response = {"history": [{"messagesAdded": [{"message": {"id": "msg1"}}]}]}
    service, history_resource, messages_resource = _build_fake_service(history_response, "msg1")
    monkeypatch.setattr(gmail_auth, "build", MagicMock(return_value=service))

    gmail_auth.fetch_mails("100")

    history_resource.list.assert_called_once_with(
        userId="me", startHistoryId="90", labelId="INBOX", historyTypes=["messageAdded"]
    )


def test_fetch_mails_skips_history_entries_without_messages_added(monkeypatch):
    monkeypatch.setattr(gmail_auth, "get_credentials", MagicMock())
    monkeypatch.setattr(gmail_auth, "_get_last_history_id", MagicMock(return_value=None))
    monkeypatch.setattr(gmail_auth, "_set_last_history_id", MagicMock())
    # Defensive case: messagesAdded missing (or explicitly None) must not
    # raise and must not fetch anything.
    history_response = {"history": [{"labelsAdded": [{"message": {"id": "msg3"}}]}, {"messagesAdded": None}]}
    service, history_resource, messages_resource = _build_fake_service(history_response, "msg3")
    monkeypatch.setattr(gmail_auth, "build", MagicMock(return_value=service))

    result = gmail_auth.fetch_mails("100")

    assert result == []
    messages_resource.get.assert_not_called()


def test_fetch_mails_fast_forwards_checkpoint_on_expired_history_id(monkeypatch):
    from googleapiclient.errors import HttpError

    monkeypatch.setattr(gmail_auth, "get_credentials", MagicMock())
    monkeypatch.setattr(gmail_auth, "_get_last_history_id", MagicMock(return_value="1"))
    set_checkpoint_mock = MagicMock()
    monkeypatch.setattr(gmail_auth, "_set_last_history_id", set_checkpoint_mock)

    fake_resp = MagicMock()
    fake_resp.status = 404
    history_resource = MagicMock()
    history_resource.list.return_value.execute.side_effect = HttpError(fake_resp, b"not found")
    users_resource = MagicMock()
    users_resource.history.return_value = history_resource
    service = MagicMock()
    service.users.return_value = users_resource
    monkeypatch.setattr(gmail_auth, "build", MagicMock(return_value=service))

    result = gmail_auth.fetch_mails("100")

    assert result == []
    set_checkpoint_mock.assert_called_once_with("100")
