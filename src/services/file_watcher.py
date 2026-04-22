import os
import time
import threading
from typing import final as sealed

from core.native_methods import NativeMethods, OVERLAPPED

@sealed
class FileWatcher:

    _thread = None
    _cts = threading.Event()
    _h_stop_event = None

    @staticmethod
    def stop_active_watcher():
        """Cancels the current watching task."""
        FileWatcher._cts.set()
        if FileWatcher._h_stop_event:
            NativeMethods.set_event(FileWatcher._h_stop_event)

        if FileWatcher._thread:
            FileWatcher._thread.join(timeout=1.0)
            FileWatcher._thread = None

    @staticmethod
    def watch_file_changes(file_to_watch, on_change_callback):
        FileWatcher._cts.clear() # Reset the Token
    
        file_to_watch = os.path.abspath(file_to_watch)
        dir_to_watch = os.path.dirname(file_to_watch)
        filename_to_watch = os.path.basename(file_to_watch)

        FileWatcher._h_stop_event = NativeMethods.create_event(manual_reset=True, initial_state=False)
        h_overlap_event = NativeMethods.create_event(manual_reset=True, initial_state=False)

        hDir = NativeMethods.open_directory_handle(dir_to_watch)
        if not hDir or hDir == NativeMethods.INVALID_HANDLE_VALUE:
            return

        overlapped = NativeMethods.create_overlapped(h_overlap_event)
        buffer = NativeMethods.create_buffer()

        try:
            while not FileWatcher._cts.is_set():
                NativeMethods.read_directory_changes(hDir, buffer, NativeMethods.byref(overlapped))

                handles = [h_overlap_event, FileWatcher._h_stop_event]
                result = NativeMethods.wait_for_multiple_objects(handles, wait_all=False)

                if result == 0:
                    raw_filename = NativeMethods.get_filename_from_notify_buffer(buffer)

                    # IMPORTANT: Check if the modified file is EXACTLY the one we care about
                    if raw_filename.lower() == filename_to_watch.lower():
                        time.sleep(0.1) 
                        on_change_callback(file_to_watch)

                    NativeMethods.reset_event(h_overlap_event)
                else:
                    NativeMethods.cancel_io(hDir)
                    break
        finally:
            # Dispose
            NativeMethods.close_handle(hDir)
            NativeMethods.close_handle(h_overlap_event)
            NativeMethods.close_handle(FileWatcher._h_stop_event)
            FileWatcher._h_stop_event = None
            print("[FileWatcher::Watch] Directory Handle Closed.")