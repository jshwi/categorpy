import subprocess

# noinspection PyPep8Naming
import PySimpleGUI as sg

from categorpy.src.torrent import torrent

ISURL = False


def get_history(key):
    try:
        global ISURL
        ISURL = True
        return torrent.read_saved(key)
    except (FileNotFoundError, KeyError):
        return key


def execute_command_subprocess(command, *args):
    sp = subprocess.Popen(
        [command, *args],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = sp.communicate()
    if out:
        print(out.decode("utf-8"))
    if err:
        print(err.decode("utf-8"))


def torrent_gui():
    url, path = get_history("url"), get_history("path")
    lenu, lenp = len(url), len(path)
    form = sg.FlexForm("Categorpy[torrent]")
    layout = [
        [
            sg.Check("Inspect", key="-INSPECT-"),
            sg.Check("Quiet", key="-QUIET-")
        ],
        [sg.T("Url", size=(15, 1)), sg.I(url, size=(lenu, 1), key="-URL-")],
        [sg.T("Path", size=(15, 1)), sg.I(path, size=(lenp, 1), key="-PATH-")],
        [sg.T("Page Number(s)", size=(15, 1)), sg.I("1", key="-PN-")],
        [sg.Output(size=(100, 20))],
        [sg.Submit("Go")],
    ]
    event, values = form.Layout(layout).Read()
    if not ISURL:
        values["Page Number(s)"].update(disabled=True)
    while True:
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        argv = [
            "--url",
            values["-URL-"],
            "--path",
            values["-PATH-"],
            "--number",
            values["-PN-"],
        ]
        for key, value in {
            "-INSPECT-": "--inspect", "-QUIET-": "--quiet"
        }.items():
            if values[key]:
                argv.append(value)
        sg.Print()
        torrent.main(argv, gui=True)
    form.close()


def main():
    layout = [
        [sg.B("Torrent")],
        [sg.B("Edit")],
        [sg.B("Clear")],
    ]
    window = sg.Window("Categorpy", layout)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        if event == "Torrent":
            torrent_gui()
    window.close()


if __name__ == "__main__":
    main()
