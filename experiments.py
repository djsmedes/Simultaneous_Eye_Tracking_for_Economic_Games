"""
@author: djs
@revision history:
    *djs 06/14 - created
    *djs 04/16 - updating documentation
"""

from threading import Event, Thread
from time import sleep
from random import choice, shuffle
from socket import gethostbyname, gethostname

from psychopy.event import waitKeys

from thepyetribe import EyeTribeServer
from pgg import PublicGoodsGame
import calibration_protocol
import instructions
import calibratable_window
import handler_communication
import screens


class ExperimentOne(object):
    """ This class will run a very specific experiment.
    """

    def __init__(self, exp_cfg_dict, exp_txt_dict, eyedata_file_name, contrib_file_name, details_file_name,
                 debug_mode=False, demo_mode=False):
        """
        :param exp_cfg_dict: contains configuration information
        :param exp_txt_dict: contains text users will see
        :param eyedata_file_name: name of the file we want to write eye tracker data to
        :param contrib_file_name: name of the file we want to write behavioral data to
        :param details_file_name: name of the file we want to write experiment details to
        :param debug_mode: if True, many safeguards are disabled, as it is assumed you know what you are doing
        :param demo_mode: if True, the program will not go fullscreen (making it easier to switch between multiple
                          applications
        """
        self.exp_cfg_dict = exp_cfg_dict
        self.exp_txt_dict = exp_txt_dict
        self.IP2num_dict = {}
        self.calibration = {}
        self.debug_mode = debug_mode
        self.demo_mode = demo_mode

        self.ID = self.exp_cfg_dict[u'exp_parameters'][u'Player ID']
        self.num_calib_points = self.exp_cfg_dict[u'exp_parameters'][u'num_calib_points']
        self.num_players = self.exp_cfg_dict[u'exp_parameters'][u'num_players']
        self.num_games = self.exp_cfg_dict[u'exp_parameters'][u'num_games']
        self.currency_per_point = self.exp_cfg_dict[u'exp_parameters'][u'currency_per_point']
        self.show_up_fee = self.exp_cfg_dict[u'exp_parameters'][u'show_up_fee']
        self.num_rounds = self.exp_cfg_dict[u'exp_parameters'][u'num_rounds']
        self.exp_version = self.exp_cfg_dict[u'exp_parameters'][u'exp_version']
        self.endowment = self.exp_cfg_dict[u'exp_parameters'][u'endowment']
        self.multipliers = self.exp_cfg_dict[u'exp_parameters'][u'multipliers']
            
        self.eyedata_file_name = eyedata_file_name
        self.contrib_file_name = contrib_file_name
        self.details_file_name = details_file_name
        
        self.handler_comm = handler_communication.ClientThread(
                host=self.exp_cfg_dict[u'exp_globals'][u'handler IP'],
                port=self.exp_cfg_dict[u'exp_globals'][u'port'],
                ID=self.ID,
                num_players=self.num_players
                )
        self.handler_comm.start()
        
        self.randomize_reward_round_and_order()
        
        self.order = self.handler_comm.get_value(u'order')
        self.reward_game = self.handler_comm.get_value(u'reward_game')
        
        temp_mult = self.multipliers[:]
        for i, order_num in enumerate(self.order):
            self.multipliers[order_num] = temp_mult[i]
        self.exp_cfg_dict[u'exp_parameters'][u'multipliers'] = self.multipliers
        
        self.et_server = EyeTribeServer()
        self.exp_cfg_dict[u'exp_parameters'][u'resolution'] = self.et_server.screenres
        self.exp_cfg_dict[u'exp_parameters'][u'framerate'] = self.et_server.framerate
        
        with open(self.details_file_name, 'a') as deets:
            for key, value in self.exp_cfg_dict[u'exp_parameters'].iteritems():
                deets.write('{}: {}\n\n'.format(key, value))
            deets.write('summary_scr_reversed: {}\n'.format(screens.FeedbackScreen.reversed))
            deets.write('# False means contributions in left column.\n\n')
                
        self.game_total_payoffs = []

        self.window = calibratable_window.CalibratableWindow(
            num_calib_points=self.num_calib_points,
            size=self.exp_cfg_dict[u'exp_parameters'][u'resolution'],
            color=self.exp_cfg_dict[u'exp_globals'][u'background_color'],
            units='pix', fullscr=(not demo_mode)
        )

    def run(self):
        """ Runs through an entire experiment.
        """

        if not self.debug_mode:
            time_est_thr = Thread(target=self.calc_and_record_time_diffs)
            time_est_thr.start()
            instructions.instructions(
                    self.window, self.exp_txt_dict, self.exp_cfg_dict,
                    self.details_file_name
                    )
            time_est_thr.join()
        screens.DetectPupilsScreen(
                disp=self.window, config_dict=self.exp_cfg_dict,
                text=self.exp_txt_dict[u'detect_pupils_screen'],
                pupil_coords_getter=self.et_server.get_pupil_locations,
                seconds_to_ok=self.exp_cfg_dict[u'detect_pupils_screen'][u'seconds_to_ok']
                ).run()
                
        self.calibration = calibration_protocol.calibrate(
            self.window, self.et_server, self.exp_txt_dict, self.exp_cfg_dict, self.debug_mode
            )            
        
        all_set_up_flag = Event()
        
        if self.calibration[u'result']:
            Thread(target=self.are_all_set_up, args=(
                    all_set_up_flag,
                    self.exp_cfg_dict[u'demo_screen'][u'duration']
                    )).start()
            self.et_server.push = True
            screens.DemoScreen(
                    disp=self.window,
                    end_event=all_set_up_flag,
                    frame_getter=lambda: self.et_server.frame
                    ).run()
            self.et_server.push = False
        else:
            Thread(target=self.are_all_set_up, args=(
                    all_set_up_flag, 0
                    )).start()
            screens.WaitScreen(
                    disp=self.window,
                    text=self.exp_txt_dict[u'wait'],
                    end_event=all_set_up_flag
                    ).run()

        other_IP_num = 1
        IPs = self.handler_comm.get_value(u'IPs')
        my_IP = gethostbyname(gethostname())
        for IP in IPs:
            if IP == my_IP:
                self.IP2num_dict[IP] = 0
            else:
                self.IP2num_dict[IP] = other_IP_num
                other_IP_num += 1
        
        with open(self.details_file_name, 'a') as deets:
            deets.write('calibration: {}\n\n'.format(self.calibration))
            deets.write('num_players: {}\n\n'.format(self.num_players))
            deets.write('my_IP: {}\n\n'.format(my_IP))
            deets.write('all_IDs: {}\n\n'.format(
                    self.handler_comm.get_value(u'IDs')
                    ))
        
        screens.ClickInstructionsScreen(
                disp=self.window,
                text=self.exp_txt_dict[u'begin_game_screen_initial'].format(self.num_rounds)
                ).run()                 
        
        contrib_screen = screens.ContribScreen(
                disp=self.window,
                text=self.exp_txt_dict[u'contrib_screen'],
                config_dict=self.exp_cfg_dict
                )
        
        all_contributions_in = Event()
        wait_screen = screens.WaitScreen(
                disp=self.window,
                text=self.exp_txt_dict[u'contrib_screen_wait'],
                end_event=all_contributions_in
                )
        
        feedback_screen = screens.FeedbackScreen(
                disp=self.window,
                num_players=self.num_players,
                config_dict=self.exp_cfg_dict
                )
            
        blank_screen = screens.BlankScreen(
                disp=self.window, duration=0.05
                )
        
        with open(self.details_file_name, 'a') as deets:
            deets.write('contribution_choice_coords: {}\n\n'.format(contrib_screen.choice_coords))
            deets.write('feedback_screen_AOI_coords: {}\n\n'.format(feedback_screen.AOI_coords))
            deets.write('continue_button_coords: {}\n\n'.format(
                    self.window.c2tl(contrib_screen.continue_button.pos)
                    ))
        
        for game_number in range(1, self.num_games+1):
            if game_number != 1:
                screens.ClickInstructionsScreen(
                        disp=self.window,
                        text=self.exp_txt_dict[u'begin_game_screen_subsequent'].format(
                                '{:n}'.format(self.multipliers[game_number-1])
                                )
                        ).run()
            game = PublicGoodsGame(
                    num_rounds=self.num_rounds,
                    num_players=self.num_players,
                    total_multiplier=self.multipliers[game_number-1],
                    endowment=self.endowment,
                    IP2num_dict=self.IP2num_dict,
                    contrib_screen=contrib_screen,
                    all_contributions_in=all_contributions_in,
                    wait_screen=wait_screen,
                    feedback_screen=feedback_screen,
                    blank_screen=blank_screen,
                    contrib_file_name=self.contrib_file_name,
                    handler_communicator=self.handler_comm
                    )
            self.et_server.push = True
            
            with open(self.eyedata_file_name.format(game_number), 'w') as et_file:
                self.et_server.record_data_to(et_file)
                game.run(previous_rounds=(game_number-1)*self.num_rounds,
                         game_number=game_number
                         )
                self.game_total_payoffs.append(game.total_payoff)
                self.et_server.record_data_to(None)
            
            self.et_server.push = False
            with open(self.details_file_name, 'a') as deets:
                deets.write('Points earned in game {}: {}\n\n'.format(game_number, game.total_payoff))
            screens.ClickInstructionsScreen(
                    disp=self.window,
                    text=self.exp_txt_dict[u'payoff_screen'].format(
                            '{:n}'.format(game.total_payoff)
                            )
                    ).run()
            screens.BlankScreen(disp=self.window, duration=0.01).run()

        reward_points = self.game_total_payoffs[self.reward_game]
        reward_cash = round(self.currency_per_point*reward_points + self.show_up_fee, 2)
        with open(self.details_file_name, 'a') as deets:
            deets.write('reward_game: {}\n'.format(self.reward_game+1))
            deets.write('reward_points: {:n}\n'.format(reward_points))
            deets.write('reward_cash: {:n}\n'.format(reward_cash))
            deets.write('# Includes 6 euro show up fee\n\n')
        
        experiment_end = Event()
        Thread(target=self.experiment_ender, args=(experiment_end,)).start()
        final_screen_text = self.exp_txt_dict[u'final_screen'].format(
                game=(self.reward_game+1),
                points='{:n}'.format(reward_points),
                cash='{:n}'.format(reward_cash)
                )
        screens.EventInstructionsScreen(
                disp=self.window,
                text=final_screen_text,
                end_event=experiment_end
                ).run()
        print 'Earnings (6 euros + amt earned in game) = {} euros.'.format(reward_cash)
        self.window.close()

    def experiment_ender(self, exp_ender_event):
        if waitKeys(['esc']):
            exp_ender_event.set()
    
    def are_all_set_up(self, all_set_up_flag, min_time=5):
        """
        :param all_set_up_flag: threading.Event which this function will set upon all players being set up.
        :param min_time: the minimum number of seconds we wait before checking if all are set up.
        """
        sleep(min_time)
        self.handler_comm.set_values({u'is_set_up': True})
        while not self.handler_comm.get_value(u'all_set_up'):
            sleep(0.250)
        all_set_up_flag.set()
    
    def calc_and_record_time_diffs(self):
        """ Calculates and records the difference in the internal clocks of the computer on which we are running the
            experiment and the of the tracker itself.
        :return: the difference in the computer's and the eye tracker's time
        """
        time_diff = self.et_server.est_cpu_minus_tracker_time()
        with open(self.details_file_name, 'a') as deets:
            deets.write('''tracker_time_offset: {}
# CPU time = tracker time + this value.\n\n'''.format(
                    time_diff
                    ))
        return time_diff
    
    def randomize_reward_round_and_order(self):
        """ Randomizes the order of the 2nd through nth multipliers, and chooses a random round to be the one in which
            the players' scores will be used to determine their reward.
        """
        seq_ = []
        for i in range(self.num_games):
            seq_.append(i)
        self.handler_comm.set_values({u'reward_game': choice(seq_)})
        seq_.remove(0)
        shuffle(seq_)
        seq_.insert(0, 0)
        self.handler_comm.set_values({u'order': seq_})
