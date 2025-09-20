from datetime import timedelta

def format_seconds_to_mmss(seconds):
    """Converts seconds to MM:SS format"""
    td = timedelta(seconds=int(seconds))
    mm, ss = divmod(td.seconds, 60)
    return f"{mm:02}:{ss:02}"