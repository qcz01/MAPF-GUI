import PySimpleGUI as sg
import re
import os
import textwrap


sg.theme('Topanga')

layout = [[sg.Text('Simple MAPF map drawer')],
          [sg.Button('Generator'), sg.Text('Input dimension X'),
           sg.InputText(default_text='8', key='-X-', size=(3, 1)), sg.Text('Y'),
           sg.InputText(default_text='8', key='-Y-', size=(3, 1))],
          [sg.HSeparator()],
          [sg.Text('Map viewer')],
          [sg.In(default_text=str(os.getcwd())+"/test.yaml", key='-VIEW-'), sg.FolderBrowse(), sg.Button('View')],
          [sg.Button('Quit')]]

window1 = sg.Window('mapDrawer', layout, finalize=True, location=(1200, 600))
window_dummy = sg.Window('map', [[]], alpha_channel=0, finalize=True)
window2 = window_dummy
DIM_X = None
DIM_Y = None

state_adding = 0  # Obs: 0, Agent: 1
state_st = 0  # start: 0, goal: 1
cmd_stack = []
num_agent = 0


def mapGenerate(x, y):
    layout = [[sg.Button('', size=(2, 2), pad=(0, 0), key=(i, j), button_color='white', metadata='Empty', tooltip=f"({i},{j})") for i in range(x)]
              for j in range(y-1, -1, -1)]
    layout2 = [[sg.Button('Obs'), sg.Button('Agent'), sg.Button('Undo'), sg.Button('Reset'), sg.Button('Done')],
               [sg.In(default_text=str(os.getcwd()) + "/test.yaml", key='-SAVE-', enable_events=True), sg.FolderBrowse()]]

    window = sg.Window('mapGen', layout + layout2, finalize=True, location=(750, 600))
    # for i in range(x):
    #     for j in range(y):
    #         window[(i, j)].bind('<B1-Enter>', 'E')
    return window

while True:
    windows, events, values = sg.read_all_windows()
    if events == sg.WIN_CLOSED or events == 'Quit':
        if windows == window2:
            window2.close()
            window2 = window_dummy
            cmd_stack = []
        else:
            break

    if windows == window2:
        if events == 'Obs':
            # adding obs
            state_adding = 0
        if events == 'Agent':
            # adding agent
            state_adding = 1

        if events == 'Reset':
            for i in range(DIM_X):
                for j in range(DIM_Y):
                    windows[(i, j)].update('', button_color='white')
                    windows[(i, j)].metadata = 'Empty'
            state_st = 0
            num_agent = 0
            cmd_stack = []

        if events == 'Undo':
            if cmd_stack:
                current = cmd_stack[-1]
                windows[current[1]].update('', button_color='white')
                windows[current[1]].metadata = 'Empty'
                if current[0] == 'Start':
                    state_st = 0
                elif current[0] == 'Goal':
                    state_st = 1
                    num_agent -= 1

                cmd_stack.pop()

        if re.match("\((.*?)\)", str(events)):
            print(events)
            if 'E' in str(events):
                # events = events[0]
                # windows[events[0]].update(button_color='black')
                # windows.refresh()
                continue
            if windows[events].metadata == 'Empty':
                if state_adding == 0:
                    windows[events].update(button_color='black')
                    windows[events].metadata = 'Obs'
                    cmd_stack.append(['Obs', events])
                else:
                    if state_st == 0:
                        windows[events].update(f'{num_agent}', button_color='red')
                        # windows[events].update(f'{num_agent}', image_filename='red.png', image_size=(8, 8))
                        state_st = 1
                        windows[events].metadata = 'Start'
                        cmd_stack.append(['Start', events])
                    else:
                        windows[events].update(f'{num_agent}', button_color='Green')
                        # windows[events].update(f'{num_agent}', image_filename='green.png', image_size=(8, 8))
                        state_st = 0
                        windows[events].metadata = 'Goal'
                        num_agent += 1
                        cmd_stack.append(['Goal', events])
            else:
                if windows[events].metadata == 'Obs':
                    windows[events].update(button_color='white')
                    windows[events].metadata = 'Empty'
                    cmd_stack.remove(['Obs', events])


        if events == 'DoneDebug':  # save the map
            if len(cmd_stack) and num_agent:
                window3 = mapGenerate(DIM_X, DIM_Y)
                window3.set_title('Validate')
                temp_num_agent = 0
                for i in range(len(cmd_stack)):
                    temp_cmd = cmd_stack[i]
                    if temp_cmd[0] == 'Start':
                        window3[temp_cmd[1]].update(f'{temp_num_agent}', button_color='red')
                    elif temp_cmd[0] == 'Goal':
                        window3[temp_cmd[1]].update(f'{temp_num_agent}', button_color='green')
                        temp_num_agent += 1
                    else:
                        window3[temp_cmd[1]].update("", button_color='black')
            else:
                sg.popup('No agents or start and goal didn`t match!',text_color='red', location=window2.current_location())

        if events == 'Done':  # save the map
            if len(cmd_stack) and num_agent:
                done_obs, done_start, done_goal = ([] for _ in range(3))
                for i in range(len(cmd_stack)):
                    if cmd_stack[i][0] == 'Obs':
                        done_obs.append(cmd_stack[i][1])
                    elif cmd_stack[i][0] == 'Start':
                        done_start.append(cmd_stack[i][1])
                    else:
                        done_goal.append(cmd_stack[i][1])
                    # cmd_stack.pop()
                #  setup json
                filename = window2['-SAVE-'].get()
                with open(filename, 'w') as f:
                    f.write('agents:\n')
                    for i in range(num_agent):
                        f.write(f"-   goal: [{done_goal[i][0]}, {done_goal[i][1]}]\n")
                        done_str = f"name: agent{i}\nstart: [{done_start[i][0]}, {done_start[i][1]}]\n"
                        f.write(textwrap.indent(done_str, '    ', lambda line: True))

                    f.write("map:\n")
                    f.write(f"    dimensions: [{DIM_X}, {DIM_Y}]\n    obstacles:\n")
                    for i in range(len(done_obs)):
                        f.write(f"    - [{done_obs[i][0]}, {done_obs[i][1]}]\n")
            else:
                sg.popup('No agents or start and goal didn`t match!',text_color='red', location=window2.current_location())

            f.close()
        if events == '-SAVE-':
            a = window2[events].get()
            if ".yaml" not in a:
                a = a + "/test.yaml"
            window2[events].update(str(a))

    if events == 'Generator':
        DIM_X = int(values['-X-'])
        DIM_Y = int(values['-Y-'])
        window2 = mapGenerate(DIM_X, DIM_Y)
        state_st = 0
        state_adding = 0
        num_agent = 0

    if events == 'View':
        filename = windows['-VIEW-'].get()
        print(filename)
        os.system(f'python3 visualize_map.py {filename} &')




window1.close()