#!/usr/bin/python
# -*- coding: utf-8 -*-

##################################################################################
# Programme de contrôle avec API ou Machine à états finis
# du robot T-Quad avec 4 roues holonomes (roues Mecanum)
# disponible à l'adresse:
# http://boutique.3sigma.fr/12-robots
#
# Auteur: 3Sigma
# Version 1.1.0 - 08/06/2017
##################################################################################

# Importe les fonctions Arduino pour Python
from pyduino import *

# Imports Généraux
import time, sched
import os
import threading
import signal
import json
import sys

# Pour la détection d'adresse IP
import socket
import fcntl
import struct

# Pour le serveur de socket
import tornado.httpserver
import tornado.ioloop
from tornado.ioloop import PeriodicCallback
import tornado.web
import tornado.websocket
import tornado.template

# Pour être sûr que Tornado a démarré
from websocket import create_connection

# Machine à états finis
from scxml.pyscxml import StateMachine

# Gestion de l'IMU
from mpu9250 import MPU9250

# Nom de l'hostname (utilisé ensuite pour savoir sur quel système
# tourne ce programme)
hostname = socket.gethostname()

# Imports pour la communication i2c avec l'Arduino Mega
from mega import Mega
mega = Mega(hostname = hostname)

# Moteurs
Nmoy = 1

omegaArriereDroit = 0.
codeurArriereDroitDeltaPos = 0
codeurArriereDroitDeltaPosPrec = 0

omegaArriereGauche = 0.
codeurArriereGaucheDeltaPos = 0
codeurArriereGaucheDeltaPosPrec = 0

omegaAvantDroit = 0.
codeurAvantDroitDeltaPos = 0
codeurAvantDroitDeltaPosPrec = 0

omegaAvantGauche = 0.
codeurAvantGaucheDeltaPos = 0
codeurAvantGaucheDeltaPosPrec = 0

# Tension effectivement appliquée
commandeArriereDroit = 0.
commandeArriereGauche = 0.
commandeAvantDroit = 0.
commandeAvantGauche = 0.

# Mode d'asservissement des moteurs en vitesse
omegarefArriereDroit = 0.
omegarefArriereGauche = 0.
omegarefAvantDroit = 0.
omegarefAvantGauche = 0.

# Mode de contrôle
mode = 0

# Saturations
umax = 6. # valeur max de la tension de commande du moteur
umin = -6. # valeur min (ou max en négatif) de la tension de commande du moteur

# Asservissements
Kplongi = 4.3 # gain proportionnel du PID d'asservissement longitudinal
Kilongi = 109.0 # gain intégral du PID d'asservissement longitudinal
Kdlongi = 0. # gain dérivé du PID d'asservissement longitudinal
Tflongi = 0.02 # constante de temps de filtrage de l'action dérivée du PID d'asservissement longitudinal
Kplat = 4.3 # gain proportionnel du PID d'asservissement latéral
Kilat = 109.0 # gain intégral du PID d'asservissement latéral
Kdlat = 0. # gain dérivé du PID d'asservissement latéral
Tflat = 0.02 # constante de temps de filtrage de l'action dérivée du PID d'asservissement latéral
Kprot = 0.37 # gain proportionnel du PID d'asservissement de rotation
Kirot = 12.5 # gain intégral du PID d'asservissement rotation
Kdrot = 0. # gain dérivé du PID d'asservissement rotation
Tfrot = 0.02 # constante de temps de filtrage de l'action dérivée du PID d'asservissement rotation
Kp = 0.05 # gain proportionnel du PID d'asservissement des moteurs
Ki = 2.5 # gain intégral du PID d'asservissement des moteurs
Kd = 0. # gain dérivé du PID d'asservissement des moteurs
Tf = 0.02 # constante de temps de filtrage de l'action dérivée du PID
I_x = [0., 0., 0., 0., 0., 0., 0.]
D_x = [0., 0., 0., 0., 0., 0., 0.]
yprec = [0., 0., 0., 0., 0., 0., 0.]
vxmes = 0.
vymes = 0.
ximes = 0.

# Paramètres mécaniques
R = 0.0225 # Rayon d'une roue
W = 0.18 # Ecart entre le centre de rotation du robot et les roues

# Variables utilisées pour les données reçues
vxref = 0.
vyref = 0.
xiref = 0.
source_ximes = 0

# Variables pour le suivi de ligne
L1 = 0.
L2 = 0.
L3 = 0.
seuil = 2.

# Timeout de réception des données
timeout = 2
timeLastReceived = 0
timedOut = False

T0 = time.time()
dt = 0.01
i = 0
tprec = time.time()
tdebut = 0
# Création d'un scheduler pour exécuter des opérations à cadence fixe
s = sched.scheduler(time.time, time.sleep)

idecimLectureTension = 0
decimLectureTension = 6000
decimErreurLectureTension = 100

# Mesure de la tension de la batterie
# On la contraint à être supérieure à 7V, pour éviter une division par
# zéro en cas de problème quelconque
lectureTensionOK = False
tensionAlim = 7.4
while not lectureTensionOK:
    try:
        tensionAlim = max(7.0, float(mega.read_battery_millivolts()) / 1000.)
        lectureTensionOK = True
    except:
        #print("Erreur lecture tension")
        pass

# Capteur de distance
idecimDistance = 0
decimDistance = 20
distance = 0
distancePrec = 0
distanceFiltre = 0
tauFiltreDistance = 0.03
    
# Initialisation de l'IMU
gz = 0.
intgz = 0.
if (hostname == "pcduino"):
    I2CBUS = 2
elif (hostname == "raspberrypi"):
    I2CBUS = 1
else:
    # pcDuino par défaut
    I2CBUS = 2
    
initIMU_OK = False
while not initIMU_OK:
    try:
        imu = MPU9250(i2cbus=I2CBUS, address=0x69)
        initIMU_OK = True
    except:
        #print("Erreur init IMU")
        pass

        
# Machine à états finis
# Recherche de l'adresse IP de l'ordinateur hôte
MEF = False
try:
    cmd = subprocess.Popen('arp', stdout=subprocess.PIPE)
    res = cmd.communicate()[0].split("\n")
    for line in res:
        if line.find("incomplete") == -1 and line.find("ether") > -1 and line.find(" C ") > -1:
            listeStr = line.split(" ")
            break
    IP = listeStr[0]
except:
    # Si erreur, on essai avec l'adresse IP locale
    IP = '127.0.0.1'

print "IP distante: " + IP

#--- setup --- 
def setup():
    
    # Initialisation des moteurs
    CommandeMoteurs(0, 0, 0, 0)
    
    
# -- fin setup -- 
 
# -- loop -- 
def loop():
    global i, T0
    i = i+1
    s.enterabs( T0 + (i * dt), 1, CalculVitesse, ())
    s.run()
# -- fin loop --

def CalculVitesse():
    global omegaArriereDroit, omegaArriereGauche, omegaAvantDroit, omegaAvantGauche, timeLastReceived, timeout, timedOut, \
        tdebut, codeurArriereDroitDeltaPos, codeurArriereGaucheDeltaPos, codeurAvantDroitDeltaPos, codeurAvantGaucheDeltaPos, \
        commandeArriereDroit, commandeArriereGauche, commandeAvantDroit, commandeAvantGauche, \
        codeurArriereDroitDeltaPosPrec, codeurArriereGaucheDeltaPosPrec, codeurAvantDroitDeltaPosPrec, codeurAvantGaucheDeltaPosPrec, tprec, \
        omegarefArriereDroit, omegarefArriereGauche, omegarefAvantDroit, omegarefAvantGauche, \
        idecimLectureTension, decimLectureTension, decimErreurLectureTension, tensionAlim, \
        distance, idecimDistance, decimDistance, distancePrec, \
        distanceFiltre, tauFiltreDistance, imu, gz, intgz, R, W, vxmes, vymes, ximes, vxref, vyref, xiref, font, source_ximes, hostname, \
        L1, L2, L3, seuil, mode, sm
    
    tdebut = time.time()
        
    # Mesure de la vitesse des moteurs grâce aux codeurs incrémentaux
    try:
        codeursDeltaPos = mega.read_codeursDeltaPos()
        codeurArriereDroitDeltaPos = codeursDeltaPos[0]
        codeurArriereGaucheDeltaPos = codeursDeltaPos[1]
        codeurAvantDroitDeltaPos = codeursDeltaPos[2]
        codeurAvantGaucheDeltaPos = codeursDeltaPos[3]
        
        # Suppression de mesures aberrantes
        if (abs(codeurArriereDroitDeltaPos - codeurArriereDroitDeltaPosPrec) > 10) or (abs(codeurArriereGaucheDeltaPos - codeurArriereGaucheDeltaPosPrec) > 10) or (abs(codeurAvantDroitDeltaPos - codeurAvantDroitDeltaPosPrec) > 10) or (abs(codeurAvantGaucheDeltaPos - codeurAvantGaucheDeltaPosPrec) > 10):
            codeurArriereDroitDeltaPos = codeurArriereDroitDeltaPosPrec
            codeurArriereGaucheDeltaPos = codeurArriereGaucheDeltaPosPrec
            codeurAvantDroitDeltaPos = codeurAvantDroitDeltaPosPrec
            codeurAvantGaucheDeltaPos = codeurAvantGaucheDeltaPosPrec


        codeurArriereDroitDeltaPosPrec = codeurArriereDroitDeltaPos
        codeurArriereGaucheDeltaPosPrec = codeurArriereGaucheDeltaPos
        codeurAvantDroitDeltaPosPrec = codeurAvantDroitDeltaPos
        codeurAvantGaucheDeltaPosPrec = codeurAvantGaucheDeltaPos
    except:
        #print "Erreur lecture codeurs"
        codeurArriereDroitDeltaPos = codeurArriereDroitDeltaPosPrec
        codeurArriereGaucheDeltaPos = codeurArriereGaucheDeltaPosPrec
        codeurAvantDroitDeltaPos = codeurAvantDroitDeltaPosPrec
        codeurAvantGaucheDeltaPos = codeurAvantGaucheDeltaPosPrec
    
    omegaArriereDroit = -2 * ((2 * 3.141592 * codeurArriereDroitDeltaPos) / 1200) / (Nmoy * dt)  # en rad/s
    omegaArriereGauche = 2 * ((2 * 3.141592 * codeurArriereGaucheDeltaPos) / 1200) / (Nmoy * dt)  # en rad/s
    omegaAvantDroit = -2 * ((2 * 3.141592 * codeurAvantDroitDeltaPos) / 1200) / (Nmoy * dt)  # en rad/s
    omegaAvantGauche = 2 * ((2 * 3.141592 * codeurAvantGaucheDeltaPos) / 1200) / (Nmoy * dt)  # en rad/s
        
    # Mesures
    vxmes = (omegaArriereDroit + omegaArriereGauche + omegaAvantDroit + omegaAvantGauche) * R / 4
    vymes = (-omegaArriereDroit + omegaArriereGauche + omegaAvantDroit - omegaAvantGauche) * R / 4
    ximes = (omegaArriereDroit - omegaArriereGauche + omegaAvantDroit - omegaAvantGauche) * R / W / 2
    
    # Lecture des capteurs de suivi de ligne
    #print " "
    try:
        # Passage des millivolts aux volts
        L1 = mega.line_read(1) / 1000.
        #print L1
        # On compare par rapport à un seuil pour savoir si le capteur voit la ligne ou non
        if L1 < seuil:
            surLigne1 = True
            if MEF:
                sm.send('L1')
        else:
            surLigne1 = False
            if MEF:
                sm.send('notL1')
    except:
        #print("Erreur lecture capteur 1")
        pass

    try:
        # Passage des millivolts aux volts
        L2 = mega.line_read(2) / 1000.
        #print L2
        # On compare par rapport à un seuil pour savoir si le capteur voit la ligne ou non
        if L2 < seuil:
            surLigne2 = True
            if MEF:
                sm.send('L2')
        else:
            surLigne2 = False
            if MEF:
                sm.send('notL2')
    except:
        #print("Erreur lecture capteur 2")
        pass
        
    try:
        # Passage des millivolts aux volts
        L3 = mega.line_read(3) / 1000.
        #print L3
        # On compare par rapport à un seuil pour savoir si le capteur voit la ligne ou non
        if L3 < seuil:
            surLigne3 = True
            if MEF:
                sm.send('L3')
        else:
            surLigne3 = False
            if MEF:
                sm.send('notL3')
    except:
        #print("Erreur lecture capteur 3")
        pass

    # Lecture de la vitesse de rotation autour de la verticale
    try:
        gyro = imu.readGyro()
        gz = gyro['z'] * math.pi / 180
    except:
        #print("Erreur lecture IMU")
        pass

    dt2 = time.time() - tprec
    tprec = time.time()
    
    # Intégration de la vitesse de rotation pour avoir l'angle
    intgz = intgz + gz * dt2
    
    # Si on n'a pas reçu de données depuis un certain temps, celles-ci sont annulées
    if (time.time()-timeLastReceived) > timeout and not timedOut:
        # Le Timoeoout est désactivé dans le cas de l'utilisation de l'API et des machines à états finis
        pass
        #timedOut = True
        
    if mode == 0:
        if timedOut:
            commandeLongi = 0.
            commandeLat = 0.
            commandeRot = 0.
        else:
            commandeLongi = PID(0, vxref, vxmes, Kplongi, Kilongi, Kdlongi, Tflongi, umax, umin, dt);
            commandeLat = PID(1, vyref, vymes, Kplat, Kilat, Kdlat, Tflat, umax, umin, dt);
            if (source_ximes == 1):
                commandeRot = PID(2, xiref, gz, Kprot, Kirot, Kdrot, Tfrot, umax, umin, dt);
            else:
                commandeRot = PID(2, xiref, ximes, Kprot, Kirot, Kdrot, Tfrot, umax, umin, dt);
        
        # Transformation des commandes longitudinales et de rotation en tension moteurs
        commandeArriereDroit = -(commandeLongi - commandeLat + commandeRot) # Tension négative pour faire tourner positivement ce moteur
        commandeArriereGauche = commandeLongi + commandeLat - commandeRot
        commandeAvantDroit = -(commandeLongi + commandeLat + commandeRot) # Tension négative pour faire tourner positivement ce moteur
        commandeAvantGauche = commandeLongi - commandeLat - commandeRot
        
        CommandeMoteurs(commandeArriereDroit, commandeArriereGauche, commandeAvantDroit, commandeAvantGauche)
        
    elif mode == 1:
        if timedOut:
            commandeArriereDroit = 0.
            commandeArriereGauche = 0.
            commandeAvantDroit = 0.
            commandeAvantGauche = 0.
        else:
            commandeArriereDroit = -PID(3, omegarefArriereDroit, omegaArriereDroit, Kp, Ki, Kd, Tf, umax, umin, dt2);
            commandeArriereGauche = PID(4, omegarefArriereGauche, omegaArriereGauche, Kp, Ki, Kd, Tf, umax, umin, dt2);
            commandeAvantDroit = -PID(5, omegarefAvantDroit, omegaAvantDroit, Kp, Ki, Kd, Tf, umax, umin, dt2);
            commandeAvantGauche = PID(6, omegarefAvantGauche, omegaAvantGauche, Kp, Ki, Kd, Tf, umax, umin, dt2);
            
        CommandeMoteurs(commandeArriereDroit, commandeArriereGauche, commandeAvantDroit, commandeAvantGauche)

            
    elif mode == 2:
        if timedOut:
            commandeArriereDroit = 0.
            commandeArriereGauche = 0.
            commandeAvantDroit = 0.
            commandeAvantGauche = 0.
            
        CommandeMoteurs(-commandeArriereDroit, commandeArriereGauche, -commandeAvantDroit, commandeAvantGauche)
            
    else:
        commandeArriereDroit = 0.
        commandeArriereGauche = 0.
        commandeAvantDroit = 0.
        commandeAvantGauche = 0.
        
        CommandeMoteurs(commandeArriereDroit, commandeArriereGauche, commandeAvantDroit, commandeAvantGauche)
    
    
    # Lecture de la tension d'alimentation
    if idecimLectureTension >= decimLectureTension:
        try:
            tensionAlim = max(7.0, float(mega.read_battery_millivolts()) / 1000.)
            idecimLectureTension = 0
        except:
            # On recommence la lecture dans decimErreurLectureTension * dt
            idecimLectureTension = idecimLectureTension - decimErreurLectureTension
            #print("Erreur lecture tension dans Loop")
    else:
        idecimLectureTension = idecimLectureTension + 1    
    
    # Calcul de la distance mesurée par le capteur ultrason
    # On fait ce calcul après l'affichage pour savoir combien de temps
    # il reste pour ne pas perturber la boucle
    if idecimDistance >= decimDistance:            
        idecimDistance = 0            
                                
        try:
            distance = mega.read_distance()
            if distance == 0:
                # Correspond en fait à une distance supérieure à 200 cm
                distance = 200
            # print "Distance: ", distance, " cm"
        except:
            print "Probleme lecture distance"
            pass
            
        # Filtre sur la distance
        distanceFiltre = (dt2 * distance + tauFiltreDistance * distancePrec) / (dt2 + tauFiltreDistance)
        distancePrec = distanceFiltre
    else:
        idecimDistance = idecimDistance + 1


    # Boucle d'exécution de la machine à états finis
    if MEF:
        eventOK = sm.datamodel["__eventOK"]
        if not sm.interpreter.exited and eventOK:
            sm.send('__e')
        
    #print time.time() - tdebut

    
def PID(iPID, ref, mes, Kp, Ki, Kd, Tf, umax, umin, dt2):
    global I_x, D_x, yprec
    
    # Calcul du PID
    # Paramètres intermédiaires
    Ti = Ki/(Kp+0.01)
    if (Kd>0): # Si PID
        ad = Tf/(Tf+dt2)
        bd = Kd/(Tf+dt2)
        Td = Kp/Kd
        Tt = sqrt(Ti*Td)
    else: # Si PI
        ad = 0
        bd = 0
        Td = 0
        Tt = 0.5*Ti
    
    br = dt2/(Tt+0.01)

    # Calcul de la commande avant saturation
        
    # Terme proportionnel
    P_x = Kp * (ref - mes)

    # Terme dérivé
    D_x[iPID] = ad * D_x[iPID] - bd * (mes - yprec[iPID])

    # Calcul de la commande avant saturation
    commande_avant_sat = P_x + I_x[iPID] + D_x[iPID]

    # Application de la saturation sur la commande
    if (commande_avant_sat > umax):
        commande = umax
    elif (commande_avant_sat < umin):
        commande = umin
    else:
        commande = commande_avant_sat
    
    # Terme intégral (sera utilisé lors du pas d'échantillonnage suivant)
    I_x[iPID] = I_x[iPID] + Ki * dt2 * (ref - mes) + br * (commande - commande_avant_sat)
    
    # Stockage de la mesure courante pour utilisation lors du pas d'échantillonnage suivant
    yprec[iPID] = mes
    
    return commande


def CommandeMoteurs(commandeArriereDroit, commandeArriereGauche, commandeAvantDroit, commandeAvantGauche):
    # Cette fonction calcule et envoi les signaux PWM au pont en H
    # en fonction des tensions de commande et d'alimentation

    global tensionAlim
    
    # L'ensemble pont en H + moteur pourrait ne pas être linéaire
    tensionArriereDroit = commandeArriereDroit
    tensionArriereGauche = commandeArriereGauche
    tensionAvantDroit = commandeAvantDroit
    tensionAvantGauche = commandeAvantGauche

    # Normalisation de la tension d'alimentation par
    # rapport à la tension d'alimentation
    tension_int_ArriereDroit = int(255 * tensionArriereDroit / tensionAlim)
    tension_int_ArriereGauche = int(255 * tensionArriereGauche / tensionAlim)
    tension_int_AvantDroit = int(255 * tensionAvantDroit / tensionAlim)
    tension_int_AvantGauche = int(255 * tensionAvantGauche / tensionAlim)

    # Saturation par sécurité
    if (tension_int_ArriereDroit > 255):
        tension_int_ArriereDroit = 255

    if (tension_int_ArriereDroit < -255):
        tension_int_ArriereDroit = -255

    if (tension_int_ArriereGauche > 255):
        tension_int_ArriereGauche = 255

    if (tension_int_ArriereGauche < -255):
        tension_int_ArriereGauche = -255

    if (tension_int_AvantDroit > 255):
        tension_int_AvantDroit = 255

    if (tension_int_AvantDroit < -255):
        tension_int_AvantDroit = -255

    if (tension_int_AvantGauche > 255):
        tension_int_AvantGauche = 255

    if (tension_int_AvantGauche < -255):
        tension_int_AvantGauche = -255

    # Commande PWM
    try:
        mega.moteursArriere(tension_int_ArriereDroit, tension_int_ArriereGauche)
        mega.moteursAvant(tension_int_AvantDroit, tension_int_AvantGauche)
        mega.moteursCRC(tension_int_ArriereDroit + tension_int_ArriereGauche, tension_int_AvantDroit + tension_int_AvantGauche)
    except:
        #print "Erreur moteurs"
        pass

    
def emitData():
    global tprec, sm, socketOK
    # Délai nécessaire pour que le serveur ait le temps de démarrer
    #delay(5000)
    # Test de connexion pour être sûr que Tornado a démarré
    while not socketOK:
        try:
            create_connection("ws://127.0.0.1:9090/ws")
        except:
            print "Attente du serveur de Websocket..."
        time.sleep(1)
        
    # Démarrage de la machine à états finis
    if MEF:
        sm = StateMachine("/root/programmes_python/scxml/fichier.scxml", IP, 15555, 0)    
        sm.start_threaded()

    tprec = time.time()
    while not noLoop: loop() # appelle fonction loop sans fin

    
class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        global socketOK
        print 'connection opened...'
        socketOK = True
        self.callback = PeriodicCallback(self.sendToSocket, 100)
        self.callback.start()
    

    def on_message(self, message):
        global vxref, vyref, xiref, source_ximes, omegarefArriereDroit, omegarefArriereGauche, omegarefAvantDroit, omegarefAvantGauche, \
            commandeArriereDroit, commandeArriereGauche, commandeAvantDroit, commandeAvantGauche, intgz, \
            timeLastReceived, timedOut, mode
            
        jsonMessage = json.loads(message)
        
        # Annulation du timeout de réception des données
        timeLastReceived = time.time()
        timedOut = False;
        
        if jsonMessage.get('mode') != None:
            # Choix du mode de commande: 0: contrôle du robot complet, 1: asservissement de vitesse des moteurs, 2: commande des moteurs en tension
            mode = int(jsonMessage.get('mode'))
            
            if mode == 0:
                if jsonMessage.get('p1') != None:
                    vxref = float(jsonMessage.get('p1'))
                else:
                    vxref = 0.
                if jsonMessage.get('p2') != None:
                    vyref = float(jsonMessage.get('p2'))
                else:
                    vyref = 0.
                if jsonMessage.get('p3') != None:
                    xiref = float(jsonMessage.get('p3')) * math.pi / 180.
                else:
                    xiref = 0.
                if jsonMessage.get('p4') != None:
                    # Choix de la source de la vitesse de rotation mesurée: 1: gyro, 0: vitesse des roues
                    source_ximes = int(jsonMessage.get('p4'))
                else:
                    source_ximes = 0
                    
            elif mode == 1:
                if jsonMessage.get('p1') != None:
                    omegarefArriereDroit = float(jsonMessage.get('p1'))
                else:
                    omegarefArriereDroit = 0.
                if jsonMessage.get('p2') != None:
                    omegarefArriereGauche = float(jsonMessage.get('p2'))
                else:
                    omegarefArriereGauche = 0.
                if jsonMessage.get('p3') != None:
                    omegarefAvantDroit = float(jsonMessage.get('p3'))
                else:
                    omegarefAvantDroit = 0.
                if jsonMessage.get('p4') != None:
                    omegarefAvantGauche = float(jsonMessage.get('p4'))
                else:
                    omegarefAvantGauche = 0.
                    
            elif mode == 2:
                if jsonMessage.get('p1') != None:
                    commandeArriereDroit = float(jsonMessage.get('p1'))
                else:
                    commandeArriereDroit = 0.
                if jsonMessage.get('p2') != None:
                    commandeArriereGauche = float(jsonMessage.get('p2'))
                else:
                    commandeArriereGauche = 0.
                if jsonMessage.get('p3') != None:
                    commandeAvantDroit = float(jsonMessage.get('p3'))
                else:
                    commandeAvantDroit = 0.
                if jsonMessage.get('p4') != None:
                    commandeAvantGauche = float(jsonMessage.get('p4'))
                else:
                    commandeAvantGauche = 0.
                
            elif mode == 3:
                if jsonMessage.get('p1') != None:
                    intgz = float(jsonMessage.get('p1'))

        if not socketOK or (mode != 0 and mode != 1 and mode != 2 and mode != 3):
            vxref = 0.
            vyref = 0.
            xiref = 0.
            source_ximes = 0
            omegarefArriereDroit = 0.
            omegarefArriereGauche = 0.
            omegarefAvantDroit = 0.
            omegarefAvantGauche = 0.
            commandeArriereDroit = 0.
            commandeArriereGauche = 0.
            commandeAvantDroit = 0.
            commandeAvantGauche = 0.
            intgz = 0.

    def on_close(self):
        global socketOK, vxref, vyref, xiref, source_ximes, omegarefArriereDroit, omegarefArriereGauche, omegarefAvantDroit, omegarefAvantGauche, \
            commandeArriereDroit, commandeArriereGauche, commandeAvantDroit, commandeAvantGauche
        print 'connection closed...'
        socketOK = False
        vxref = 0.
        vyref = 0.
        xiref = 0.
        source_ximes = 0
        omegarefArriereDroit = 0.
        omegarefArriereGauche = 0.
        omegarefAvantDroit = 0.
        omegarefAvantGauche = 0.
        commandeArriereDroit = 0.
        commandeArriereGauche = 0.
        commandeAvantDroit = 0.
        commandeAvantGauche = 0.

    def sendToSocket(self):
        global socketOK, vxmes, vymes, ximes, omegaArriereDroit, omegaArriereGauche, omegaAvantDroit, omegaAvantGauche, \
            gz, intgz, L1, L2, L3, seuil
        
        tcourant = time.time() - T0
        aEnvoyer = json.dumps({'Temps':("%.2f" % tcourant), \
                                'omegaArriereDroit':("%.2f" % omegaArriereDroit), \
                                'omegaArriereGauche':("%.2f" % omegaArriereGauche), \
                                'omegaAvantDroit':("%.2f" % omegaAvantDroit), \
                                'omegaAvantGauche':("%.2f" % omegaAvantGauche), \
                                'vxmes':("%.2f" % vxmes), \
                                'vymes':("%.2f" % vymes), \
                                'ximes':("%.2f" % ximes), \
                                'distance':("%d" % distance), \
                                'distanceFiltre':("%d" % distanceFiltre), \
                                'gz':("%.2f" % gz), \
                                'psi':("%.2f" % intgz), \
                                'L1':("%.1f" % L1), \
                                'L2':("%.1f" % L2), \
                                'L3':("%.1f" % L3), \
                                'seuil':("%.1f" % seuil), \
                                'Raw':("%.2f" % tcourant) \
                                + "," + ("%.2f" % omegaArriereDroit) \
                                + "," + ("%.2f" % omegaArriereGauche) \
                                + "," + ("%.2f" % omegaAvantDroit) \
                                + "," + ("%.2f" % omegaAvantGauche) \
                                + "," + ("%.2f" % vxmes) \
                                + "," + ("%.2f" % vymes) \
                                + "," + ("%.2f" % ximes) \
                                + "," + ("%d" % distance) \
                                + "," + ("%d" % distanceFiltre) \
                                + "," + ("%.2f" % gz) \
                                + "," + ("%.2f" % intgz) \
                                + "," + ("%.1f" % L1) \
                                + "," + ("%.1f" % L2) \
                                + "," + ("%.1f" % L3) \
                                })
                                
        if socketOK:
            try:
                self.write_message(aEnvoyer)
            except:
                pass
            
    def check_origin(self, origin):
        # Voir http://www.tornadoweb.org/en/stable/websocket.html#tornado.websocket.WebSocketHandler.check_origin
        # et http://www.arundhaj.com/blog/tornado-error-during-websocket-handshake.html
        return True        

    
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
    
application = tornado.web.Application([
    (r'/ws', WSHandler)
])

def startTornado():
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(9090)
    tornado.ioloop.IOLoop.instance().start()


# Gestion du CTRL-C
def signal_handler(signal, frame):
    global vxref, vyref, xiref, source_ximes, omegarefArriereDroit, omegarefArriereGauche, omegarefAvantDroit, omegarefAvantGauche, \
            commandeArriereDroit, commandeArriereGauche, commandeAvantDroit, commandeAvantGauche
    print 'Sortie du programme'
    vxref = 0.
    vyref = 0.
    xiref = 0.
    source_ximes = 0
    omegarefArriereDroit = 0.
    omegarefArriereGauche = 0.
    omegarefAvantDroit = 0.
    omegarefAvantGauche = 0.
    commandeArriereDroit = 0.
    commandeArriereGauche = 0.
    commandeAvantDroit = 0.
    commandeAvantGauche = 0.
    CommandeMoteurs(0, 0, 0, 0)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

#--- obligatoire pour lancement du code -- 
if __name__=="__main__": # pour rendre le code executable
    # Traitement des arguments d'entrée
    # S'il y en a au moins un et si le premier est égale à 1, 
    # on est dans le mode Machine à états finis
    if len(sys.argv) > 1 and int(sys.argv[1]) == 1:
        print "Mode Machine à Etats Finis"
        MEF = True
    else:
        print "Mode API"
        MEF = False

    socketOK = False
    setup() # appelle la fonction setup
    print "Setup done."
    
    th = threading.Thread(None, emitData, None, (), {})
    th.daemon = True
    th.start()
    
    print "Starting Tornado."
    try:
        print "Connect to ws://" + get_ip_address('eth0') + ":9090/ws with Ethernet."
        pass
    except:
        pass
        
    try:
        print "Connect to ws://" + get_ip_address('wlan0') + ":9090/ws with Wifi."
        pass
    except:
        pass
    startTornado()


