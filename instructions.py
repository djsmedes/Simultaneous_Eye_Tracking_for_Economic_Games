"""
@author: djs
@revision history:
    *djs 07/14 - created
    *djs 04/16 - updating documentation
"""

from psychopy.visual import ImageStim, Rect

import screens


def instructions(window, exp_txt_dict, exp_cfg_dict, details_file_name, text_w=800):
    """ The instruction sequence for a particular experiment.
    :param window: PsychoPy Window
    :param exp_txt_dict: contains text strings the user will see
    :param exp_cfg_dict: contains configuration data
    :param details_file_name: name of file to write details to
    :param text_w: width of the text
    """
    for i in range(1, 6):
        key_i = 'instructions_{}'.format(i)
        txt_ = exp_txt_dict[key_i]
        if i == 2:
            txt_ = txt_.format(
                    '{:n}'.format(
                            round(1.0/exp_cfg_dict[u'exp_parameters'][u'currency_per_point'], 0)
                            )
                    )
        screens.ClickInstructionsScreen(
                disp=window,
                text=txt_,
                ).run()
    for i in range(1, 7):
        screens.ImageScreen(
                disp=window,
                text='',
                text_width=100,
                image='resources/visual_explanation/Slide{}.PNG'.format(i),
                image_size=(960, 720),
                image_pos=(0, 100)
                ).run()
    screens.ImageScreen(
            disp=window,
            text=exp_txt_dict['instructions_6'],
            text_width=text_w,
            image='resources/equation.PNG',
            image_size=(960, 100),
            text_pos=(0, -100),
            image_pos=(0, 100)
            ).run()
    control_questions(window, exp_txt_dict, details_file_name)
    background = Rect(
            win=window,
            width=970,
            height=550,
            fillColor='white',
            lineColor=None,
            pos=(430, 50)
            )
    if screens.FeedbackScreen.reversed:
        folder = 'reversed'
    else:
        folder = 'default'
    for i in range(9):
        key_i = 'summary_{}'.format(i)
        extra_img = [background]
        image_name = 'resources/feedback/{0}/Slide{1}.PNG'.format(folder, i)
        if i == 0:
            image_name = 'resources/contrib_screen.PNG'
        if i == 6 or i == 7:
            extra_img.append(ImageStim(
                    win=window,
                    image='resources/equation_with_numbers.PNG', 
                    pos=(-480, 0)
                    ))
        screens.ImageScreen(
                disp=window,
                text=exp_txt_dict[key_i],
                text_width=text_w - 25,
                image=image_name,
                image_size=(960, 540),
                text_pos=(-500, 0),
                image_pos=(430, 50),
                extra_image_stims=extra_img
                ).run()
    screens.ClickInstructionsScreen(
                disp=window,
                text=exp_txt_dict['pre_calibration_instructions']
                ).run()
                    
                    
def control_questions(window, exp_txt_dict, details_file_name):
    """ Asks users a set of control questions to make sure they were paying attention.
    :param window: PsychoPy Window
    :param exp_txt_dict: contains text strings the user will see
    :param details_file_name: file to write details to
    """
    correct_ans = [
            [0, 0],
            [20, 20],
            [36, 36],
            [19, 28, 37]
            ]
    equation = ImageStim(
            win=window,
            image='resources/equation.PNG',
            pos=(0, 400)
            )
    for i in range(1, 4):
        key_i = 'control_q_{}'.format(i)
        txts = exp_txt_dict[key_i].split('$$')
        ctrl_q_scrn = screens.KeyboardInputScreen(
                disp=window,
                text=txts[0],
                input_prompt_list=txts[1:],
                correct_ans_list=correct_ans[i],
                extra_draw_list=[equation]
                )
        ctrl_q_scrn.run()
        all_correct = True
        for index, ans_ in enumerate(ctrl_q_scrn.answer_list):
            if float(ans_.replace(',', '.')) != correct_ans[i][index]:
                all_correct = False
                ctrl_q_scrn.input_field_list[index]._frame.fillColor = 'indianred'
            else:
                ctrl_q_scrn.input_field_list[index]._frame.fillColor = 'palegreen'
        if not all_correct:
            screens.ClickInstructionsScreen(
                    disp=window,
                    text=exp_txt_dict[u'control_q_wrong'],
                    wait_time=1
                    ).run()
            ctrl_q_scrn.run()
        with open(details_file_name, 'a') as deets:
            deets.write('Control Q 1 answers: {}\n'.format(ctrl_q_scrn.answer_list))
    with open(details_file_name, 'a') as deets:
            deets.write('\n')
