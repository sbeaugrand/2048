from kivy.utils import platform

class Achievement():
	def __init__(self, app):
		self.app = app
		self.platform = platform()

		if self.platform == 'android':
			# Support for Google Play
			import gs_android
			leaderboard_highscore = 'CgkI0InGg4IYEAIQBg'
			achievement_block_32 = 'CgkI0InGg4IYEAIQCg'
			achievement_block_64 = 'CgkI0InGg4IYEAIQCQ'
			achievement_block_128 = 'CgkI0InGg4IYEAIQAQ'
			achievement_block_256 = 'CgkI0InGg4IYEAIQAg'
			achievement_block_512 = 'CgkI0InGg4IYEAIQAw'
			achievement_block_1024 = 'CgkI0InGg4IYEAIQBA'
			achievement_block_2048 = 'CgkI0InGg4IYEAIQBQ'
			achievement_block_4096 = 'CgkI0InGg4IYEAIQEg'
			achievement_100x_block_512 = 'CgkI0InGg4IYEAIQDA'
			achievement_1000x_block_512 = 'CgkI0InGg4IYEAIQDQ'
			achievement_100x_block_1024 = 'CgkI0InGg4IYEAIQDg'
			achievement_1000x_block_1024 = 'CgkI0InGg4IYEAIQDw'
			achievement_10x_block_2048 = 'CgkI0InGg4IYEAIQEA'
			achievements = {
				32: achievement_block_32,
				64: achievement_block_64,
				128: achievement_block_128,
				256: achievement_block_256,
				512: achievement_block_512,
				1024: achievement_block_1024, 
				2048: achievement_block_2048,
				4096: achievement_block_4096}

			from kivy.uix.popup import Popup
			class GooglePlayPopup(Popup):
				pass

		else:
			achievements = {}
			
	def register(self, app, value):
		if self.platform == 'android':
			if value in achievements:
				app.gs_unlock(achievements[value])
			if value == 512:
				app.gs_increment(achievement_100x_block_512)
				app.gs_increment(achievement_1000x_block_512)
			elif value == 1024:
				app.gs_increment(achievement_100x_block_1024)
				app.gs_increment(achievement_1000x_block_1024)
			elif value == 2048:
				app.gs_increment(achievement_10x_block_2048)
				
	def set_config(self, config):
		if platform == 'android':
			config.setdefaults('play', {'use_google_play': '0'})
			
	def use_google_play(self):
		return self.use_google_play
	
	def setup_ui(self):
		print "---in setup_ui"
		if platform == 'android':
			self.use_google_play = self.config.getint('play', 'use_google_play')
			if self.use_google_play:
				gs_android.setup(self.app)
			else:
				Clock.schedule_once(self.ask_google_play, .5)
		else:
			# remove all the leaderboard and achievement buttons
			scoring = self.app.root.ids.scoring
			scoring.parent.remove_widget(scoring)
			
	def gs_increment(self, uid):
		if platform == 'android' and self.use_google_play:
			gs_android.increment(uid, 1)

	def gs_unlock(self, uid):
		if platform == 'android' and self.use_google_play:
			gs_android.unlock(uid)

	def gs_score(self, score):
		if platform == 'android' and self.use_google_play:
			gs_android.leaderboard(leaderboard_highscore, score)

	def gs_show_achievements(self):
		if platform == 'android':
			if self.use_google_play:
				gs_android.show_achievements()
			else:
				self.ask_google_play()

	def gs_show_leaderboard(self):
		if platform == 'android':
			if self.use_google_play:
				gs_android.show_leaderboard(leaderboard_highscore)
			else:
				self.ask_google_play()

	def ask_google_play(self, *args):
		popup = GooglePlayPopup()
		popup.open()

	def activate_google_play(self):
		self.config.set('play', 'use_google_play', '1')
		self.config.write()
		self.use_google_play = 1
		gs_android.setup(self)
		
	def on_pause(self):
		if platform == 'android':
			gs_android.on_stop()

	def on_resume(self):
		if platform == 'android':
			gs_android.on_start()

