"""
@author: djs
@revision history:
    *djs 07/14 - created
    *djs 04/16 - updating documentation
"""

import screens


def calibrate(window, et_server, exp_txt_dict, exp_cfg_dict, debug_mode=False):
    """ The calibration protocol used in our experiment. Three attempts at a successful calibration are made. If all
        three attmpets fail, we just continue the experiment so that we can at least get data on one subject.
    :param window: PsychoPy Window
    :param et_server: thepyetribe.EyeTribeServer
    :param exp_txt_dict: contains strings to show to users
    :param exp_cfg_dict: contains configuration data
    :param debug_mode: boolean parameter; if True, many safeguards are not in place because it is assumed you know what
                       you're doing
    :return: the calibration object
    """
    window.flip()
    if debug_mode:  # no need to redo the calibration if we already have one - debug mode does not need to be accurate
        if et_server.iscalibrated:
            calibresult = et_server.calibresult
            if calibresult[u'result']:
                return calibresult
    else:
        et_server.clear_calibration()
        
    screens.TimedInstructionsScreen(
                disp=window, disp_time=2.5,
                text=exp_txt_dict[u'calibration_look']
                ).run()
    calib = window.calibrate(et_server)
                                            
    if calib[u'result']:
        return calib
    else:
        screens.ClickInstructionsScreen(
                    disp=window, wait_time=2,
                    text=exp_txt_dict[u'calibration_failed']
                    ).run()
        screens.TimedInstructionsScreen(
                disp=window, disp_time=2.5,
                text=exp_txt_dict[u'calibration_look']
                ).run()
        calib = window.calibrate(et_server)
            
    if calib[u'result']:
        return calib
    else:
        screens.ClickInstructionsScreen(
                disp=window, wait_time=2,
                text=exp_txt_dict[u'calibration_failed_again']
                ).run()
        screens.DetectPupilsScreen(
                disp=window, config_dict=exp_cfg_dict,
                text=exp_txt_dict[u'detect_pupils_screen'],
                pupil_coords_getter=et_server.get_pupil_locations,
                seconds_to_ok=exp_cfg_dict[u'detect_pupils_screen'][u'seconds_to_ok']
                ).run()
        screens.TimedInstructionsScreen(
                disp=window, disp_time=2.5,
                text=exp_txt_dict[u'calibration_look']
                ).run()
        calib = window.calibrate(et_server)
        
    return calib
