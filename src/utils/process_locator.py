from core.native_methods import NativeMethods

class ProcessLocator:

    @staticmethod
    def get_process_pid(process_name):
        pids = NativeMethods.get_all_pids()
        
        for pid in pids:
            if pid == 0:
                continue
                
            if NativeMethods.get_process_name(pid) == process_name:
                return pid
                
        return None