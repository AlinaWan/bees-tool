# Technical Debt Register

This file tracks known technical debt in this project.

## 1. Concurrency Management and UI Modality
* **Problem:** The application crashes if a user interacts with the main menu while a modal message box is active.
    * **Error Message:**
      ```powershell
      Fatal Python error: PyEval_RestoreThread: the function must be called with the GIL held, after Python initialization and before Python finalization, but the GIL is released (the current Python thread state is NULL)
      Python runtime state: initialized

      Thread 0x00006754 [Thread-8] (most recent call first):
        File "core\native_methods.py", line 477 in get_message
        File "services\hotkey_listener.py", line 52 in run
        File "pythoncore-3.14-64\Lib\threading.py", line 1082 in _bootstrap_inner
        File "pythoncore-3.14-64\Lib\threading.py", line 1044 in _bootstrap

      Thread 0x00005e54 [Thread-7 (_watch_loop)] (most recent call first):
        File "core\native_methods.py", line 259 in wait_for_multiple_objects
        File "services\file_watcher.py", line 62 in _watch_loop
        File "pythoncore-3.14-64\Lib\threading.py", line 1024 in run
        File "pythoncore-3.14-64\Lib\threading.py", line 1082 in _bootstrap_inner
        File "pythoncore-3.14-64\Lib\threading.py", line 1044 in _bootstrap

      Current thread 0x00007694 (most recent call first):
        File "core\native_methods.py", line 277 in message_box
        File "program.pyw", line 274 in run
        File "program.pyw", line 567 in main
        File "program.pyw", line 600 in <module>

      Extension modules: numpy._core._multiarray_umath, numpy.linalg._umath_linalg, markupsafe._speedups (total: 3)
      ```
* **Solution:** Every single `NativeMethods.message_box` call must happen on the main thread, and background threads must use a thread-safe queue to request a message box.
* **Priority:** Low
* **Date of Entry:** 2026-04-26 (*Updated 2026-04-26*)