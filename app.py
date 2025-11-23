httpx.ReadError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/interview_practice_partners/app.py", line 125, in <module>
    response = st.session_state.chat_session.send_message(
        initial_prompt
    )
File "/home/adminuser/venv/lib/python3.13/site-packages/google/genai/chats.py", line 254, in send_message
    response = self._modules.generate_content(
        model=self._model,
        contents=self._curated_history + [input_content],  # type: ignore[arg-type]
        config=config if config else self._config,
    )
File "/home/adminuser/venv/lib/python3.13/site-packages/google/genai/models.py", line 5218, in generate_content
    response = self._generate_content(
        model=model, contents=contents, config=parsed_config
    )
File "/home/adminuser/venv/lib/python3.13/site-packages/google/genai/models.py", line 4000, in _generate_content
    response = self._api_client.request(
        'post', path, request_dict, http_options
    )
File "/home/adminuser/venv/lib/python3.13/site-packages/google/genai/_api_client.py", line 1388, in request
    response = self._request(http_request, http_options, stream=False)
File "/home/adminuser/venv/lib/python3.13/site-packages/google/genai/_api_client.py", line 1224, in _request
    return self._retry(self._request_once, http_request, stream)  # type: ignore[no-any-return]
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/tenacity/__init__.py", line 477, in __call__
    do = self.iter(retry_state=retry_state)
File "/home/adminuser/venv/lib/python3.13/site-packages/tenacity/__init__.py", line 378, in iter
    result = action(retry_state)
File "/home/adminuser/venv/lib/python3.13/site-packages/tenacity/__init__.py", line 420, in exc_check
    raise retry_exc.reraise()
          ~~~~~~~~~~~~~~~~~^^
File "/home/adminuser/venv/lib/python3.13/site-packages/tenacity/__init__.py", line 187, in reraise
    raise self.last_attempt.result()
          ~~~~~~~~~~~~~~~~~~~~~~~~^^
File "/usr/local/lib/python3.13/concurrent/futures/_base.py", line 449, in result
    return self.__get_result()
           ~~~~~~~~~~~~~~~~~^^
File "/usr/local/lib/python3.13/concurrent/futures/_base.py", line 401, in __get_result
    raise self._exception
File "/home/adminuser/venv/lib/python3.13/site-packages/tenacity/__init__.py", line 480, in __call__
    result = fn(*args, **kwargs)
File "/home/adminuser/venv/lib/python3.13/site-packages/google/genai/_api_client.py", line 1194, in _request_once
    response = self._httpx_client.request(
        method=http_request.method,
    ...<3 lines>...
        timeout=http_request.timeout,
    )
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_client.py", line 825, in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_client.py", line 914, in send
    response = self._send_handling_auth(
        request,
    ...<2 lines>...
        history=[],
    )
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_client.py", line 942, in _send_handling_auth
    response = self._send_handling_redirects(
        request,
        follow_redirects=follow_redirects,
        history=history,
    )
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_client.py", line 979, in _send_handling_redirects
    response = self._send_single_request(request)
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_client.py", line 1014, in _send_single_request
    response = transport.handle_request(request)
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_transports/default.py", line 249, in handle_request
    with map_httpcore_exceptions():
         ~~~~~~~~~~~~~~~~~~~~~~~^^
File "/usr/local/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_transports/default.py", line 118, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
