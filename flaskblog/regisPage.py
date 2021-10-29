class RegisPage:
	def __init__(self):
		self.webCamOff = True
		self.counter = 0
		self.faces = []
		self.grayFaces = []
		self.emb_path=[]
		self.img_path=[]
		self.max_counter = 5
		self.file_path = os.path.join(os.getcwd(), "DB")
		self.dynamic_img=[]
		self.takePicture()

	def popUpNama(self):
		screen_width = win.winfo_screenwidth()
		screen_height = win.winfo_screenheight()

		size = tuple(int(_) for _ in win.geometry().split('+')[0].split('x'))
		
		x = screen_width/2 - size[0]/2
		y = screen_height/2 - size[0]/2

		win.geometry("+%d+%d" %(x,y))

		win.mainloop()


	def stop (self):
		self.fps.stop()
		self.webCamOff = True
		self.vs.stream.release()
		cv2.destroyAllWindows()
		self.stopEvent.set()
		self.panel.pack_forget()
		self.StopBut.pack_forget()
		self.TakePicBut.pack_forget()
		
	def videoLoop(self):
		detector= MTCNN()
		self.bounding_box = None
		self.fps = FPS().start()
		try:
			while not self.stopEvent.is_set():
				self.frame = self.vs.read()
				self.frame = imutils.resize(self.frame, width=500, height=500)
				image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
				result = detector.detect_faces(image)

				if result != []:
		  			for person in result:
		  				self.bounding_box = person['box']
		  				keypoints = person['keypoints']
		  				cv2.rectangle(image, (self.bounding_box[0], self.bounding_box[1]),
		  							(self.bounding_box[0]+self.bounding_box[2], self.bounding_box[1] + self.bounding_box[3]),
		  							(0,155,255),2)

				image = Image.fromarray(image)
				image = ImageTk.PhotoImage(image)

				self.fps.update()

		except RuntimeError :
			print("[INFO] caught Runtime Error")


	def takePhoto(self):

		self.face = self.frame[self.bounding_box[1]:self.bounding_box[1] + self.bounding_box[3],self.bounding_box[0]:self.bounding_box[0]+self.bounding_box[2]]
		self.resized_face = cv2.resize(self.face, (96,96), interpolation = cv2.INTER_AREA)
		self.faces.append(cv2.cvtColor(self.resized_face, cv2.COLOR_BGR2RGB))
		self.gray_face = cv2.cvtColor(self.resized_face, cv2.COLOR_BGR2GRAY)
		self.gray_face = img_to_array(self.gray_face).astype('float32')/255

		self.grayFaces.append(self.gray_face)

		self.counter +=1
		print("GRAY FACES: ", np.array(self.grayFaces).shape)
		print("FACES: ",np.array(self.faces).shape)
		print("Counter: " , self.counter)
		# self.stop()
		self.loadImage()
	################### 

	def cancelPhoto(self):
		self.counter-=1
		# print("COUNTER:",self.counter)
		del self.grayFaces[-1]
		# print(np.array(self.grayFaces).shape)
		del self.faces[-1]
		# print(np.array(self.faces).shape)
		
		self.dynamic_img[self.counter].destroy()
		del self.dynamic_img[-1]
		print("DYNAMIC:",len(self.dynamic_img))

		if(self.counter == 0):
			self.saveBut.pack_forget()
			self.cancelBut.pack_forget()
		self.cancelBut.config(state="active")

	def loadImage(self):
		# self.addBut.grid_forget()
		self.saveBut.pack_forget()
		self.cancelBut.pack_forget()

		if(self.counter > 0):
			face = np.array(self.faces)
			# print("FACE SHAPE:",face.shape)

			render = ImageTk.PhotoImage(image=Image.fromarray(face[face.shape[0]-1]))
			img = Label(self.f1, image=render)
			self.dynamic_img.append(img)
			img.image = render
			img.pack(padx=15, pady=(5))

		if(self.counter != self.max_counter):
			self.saveBut.config(state="disabled")
		if(self.counter == self.max_counter):
			self.saveBut.config(state="normal")
			self.TakePicBut.config(state="disabled")

	def takePicture(self):
		if self.counter < self.max_counter:

			if self.webCamOff:
				print("Opening Webcam")
				self.webCamOff = False
				self.stopEvent = threading.Event()
				self.panel = None
				self.StopBut = None
				self.vs  = VideoStream(src=0).start()
				self.thread = threading.Thread(target=self.videoLoop)
				self.thread.start()

		else:
			messagebox.showinfo("INFO", "Jumlah Maksimum Foto adalah "+str(self.max_counter))

	def clear_entry(self):
		self.vs.stream.release()
		self.stopEvent.set()
		self.webCamOff = True
		self.cancelBut.invoke()