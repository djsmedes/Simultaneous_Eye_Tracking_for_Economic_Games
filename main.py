"""
@author: djs
@revision history:
    *djs 07/14 - created
    *djs 04/16 - updating documentation
"""

import yaml
import threading
import locale
from sys import exit

from psychopy import gui

import experiments


def _quit_all():
    alive_threads = threading.enumerate()
    for thread in alive_threads:
        if isinstance(thread, threading._MainThread):
            continue
        else:
            try:
                thread.stop()
            except AttributeError:
                print 'AttributeError: {} does not have a stop() method.'.format(repr(thread))
    locale.setlocale(locale.LC_ALL, '')
    exit(0)

# SCRIPT BEGINS HERE

init_dlg = gui.Dlg(title='EyeGames')
init_dlg.addField('Subject ID')
init_dlg.addField('Sprache', choices=['deutsch', 'english'])
init_dlg.addField('Mode', choices=['experiment', 'demo', 'debug'])
init_dlg.show()
if init_dlg.OK:
    demo_mode = False
    debug_mode = False
    if init_dlg.data[2] == 'demo':
        demo_mode = True
    elif init_dlg.data[2] == 'debug':
        demo_mode = True
        debug_mode = True
    
    cfg_file = 'EyeGames.cfg'
    stream1 = file(cfg_file)
    exp_cfg_dict = yaml.load(stream1)
    stream1.close()
    header_str = ''
    for i in range(1, exp_cfg_dict[u'exp_parameters'][u'num_players']):
        header_str += 'opponent_{}_contrib, '.format(i)
    
    txt_file = 'resources/{}/exp_text.txt'.format(init_dlg.data[1])
    stream2 = file(txt_file)
    exp_txt_dict = yaml.load(stream2)
    stream2.close()
    
    if init_dlg.data[1] == 'english':
        locale.setlocale(locale.LC_ALL, locale='English_United States')
    elif init_dlg.data[1] == 'deutsch':
        locale.setlocale(locale.LC_ALL, locale='German_Germany')

    own_ID = init_dlg.data[0]
    exp_cfg_dict[u'exp_parameters'][u'Player ID'] = own_ID

    # FILES ERASED IF THEY ALREADY EXIST.
    # Is this wise? I don't know.
    eyedata_file_name = 'data/{0}_game_{1}_ET.txt'.format(own_ID, '{}')
    contrib_file_name = 'data/{}_contributions.txt'.format(own_ID)
    with open(contrib_file_name, 'w') as contribs:
        contribs.write(
                'game, round, contribution, ' + header_str + 'payoff, '
                'choice_screen_onset, choice_screen_ended, '
                'summary_screen_onset, summary_screen_ended\n'
                )
    details_file_name = 'data/{}_details.txt'.format(own_ID)
    with open(details_file_name, 'w'):
        pass
    
    new_experiment = experiments.ExperimentOne(
                exp_cfg_dict=exp_cfg_dict,
                exp_txt_dict=exp_txt_dict,
                eyedata_file_name=eyedata_file_name,
                contrib_file_name=contrib_file_name,
                details_file_name=details_file_name,
                debug_mode=debug_mode,
                demo_mode=demo_mode
                )
    new_experiment.run()
    _quit_all()

else:
    _quit_all()
