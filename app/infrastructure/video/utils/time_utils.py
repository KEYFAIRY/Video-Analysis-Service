from datetime import timedelta

def format_seconds_to_mmss(seconds):
    """Convierte segundos a formato MM:SS"""
    td = timedelta(seconds=int(seconds))
    mm, ss = divmod(td.seconds, 60)
    return f"{mm:02}:{ss:02}"