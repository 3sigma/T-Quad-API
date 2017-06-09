# -*- coding: utf-8 -*-

##################################################################################
# API de pilotage du robot T-Quad avec 4 roues holonomes (roues Mecanum)
# disponible à l'adresse:
# http://boutique.3sigma.fr/12-robots
#
# Auteur: 3Sigma
# Version 1.1.0 - 08/06/2017
##################################################################################

from websocket import create_connection
import math
import time
import json
import sched
import threading

class TQuad_API:

    def __init__(self):

        # Attente de démarrage du serveur de Websocket
        socketOK = False
        while not socketOK:
            try:
                self.ws = create_connection("ws://127.0.0.1:9090/ws")
                socketOK = True
            except:
                pass
            time.sleep(1)
        
        self.message = ""
        self.started = True
        
        # Scheduler
        self.T0 = time.time()
        self.i = 0
        self.dt = 0.01
        self.s = sched.scheduler(time.time, time.sleep)
        
        # Thread de lecture du websocket
        self._lectureWS() # Initialisation indispensable
        th = threading.Thread(None, self._loop, None, (), {})
        th.daemon = True
        th.start()
        
    
    def _loop(self):
        while self.started:
            self.i = self.i + 1
            self.s.enterabs(self.T0 + (self.i * self.dt), 1, self._lectureWS, ())
            self.s.run()
        
        
    def _lectureWS(self):
        self.message =  self.ws.recv()
        #print "Received '%s'" % self.message
        
        
    def TensionMoteurArriereDroit(self, tension, duree = -1):
        pmin = -6
        pmax = 6
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(tension))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 2, "p1": ' + str(p1) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 2, "p1": 0}')
            
            
    def TensionMoteurArriereGauche(self, tension, duree = -1):
        pmin = -6
        pmax = 6
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p2 = eval(str(tension))
            # Saturations min et max
            p2 = max(min(pmax, p2), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 2, "p2": ' + str(p2) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 2, "p2": 0}')
            
            
    def TensionMoteurAvantDroit(self, tension, duree = -1):
        pmin = -6
        pmax = 6
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p3 = eval(str(tension))
            # Saturations min et max
            p3 = max(min(pmax, p3), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 2, "p3": ' + str(p3) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 2, "p3": 0}')
            
            
    def TensionMoteurAvantGauche(self, tension, duree = -1):
        pmin = -6
        pmax = 6
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p4 = eval(str(tension))
            # Saturations min et max
            p4 = max(min(pmax, p4), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 2, "p4": ' + str(p4) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 2, "p4": 0}')
            
            
    def TensionMoteurs(self, tensionArriereDroit, tensionArriereGauche, tensionAvantDroit, tensionAvantGauche, duree = -1):
        pmin = -6
        pmax = 6
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(tensionArriereDroit))
            p2 = eval(str(tensionArriereGauche))
            p3 = eval(str(tensionAvantDroit))
            p4 = eval(str(tensionAvantGauche))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            p2 = max(min(pmax, p2), pmin)
            p3 = max(min(pmax, p3), pmin)
            p4 = max(min(pmax, p4), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 2, "p1": ' + str(p1) + ', "p2": ' + str(p2) + ', "p3": ' + str(p3) + ', "p4": ' + str(p4) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 2, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
            
            
    def TensionMouvementLongitudinal(self, tension, duree = -1):
        pmin = -6
        pmax = 6
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(tension))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 2, "p1": ' + str(p1) + ', "p2": ' + str(p1) + ', "p3": ' + str(p1) + ', "p4": ' + str(p1) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 2, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
            
            
    def TensionMouvementLateral(self, tension, duree = -1):
        pmin = -6
        pmax = 6
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(tension))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 2, "p1": ' + str(-p1) + ', "p2": ' + str(p1) + ', "p3": ' + str(p1) + ', "p4": ' + str(-p1) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 2, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
            
            
    def TensionMouvementPivot(self, tension, duree = -1):
        pmin = -6
        pmax = 6
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(tension))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 2, "p1": ' + str(p1) + ', "p2": ' + str(-p1) + ', "p3": ' + str(p1) + ', "p4": ' + str(-p1) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 2, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
            
            
    def TensionMouvement(self, tensionMouvementLongitudinal, tensionMouvementLateral, tensionMouvementPivot, duree = -1):
        pmin = -6
        pmax = 6
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(tensionMouvementLongitudinal))
            p2 = eval(str(tensionMouvementLateral))
            p3 = eval(str(tensionMouvementPivot))
            tensionArriereDroit = tensionMouvementLongitudinal - tensionMouvementLateral + tensionMouvementPivot
            tensionArriereGauche = tensionMouvementLongitudinal + tensionMouvementLateral - tensionMouvementPivot
            tensionAvantDroit = tensionMouvementLongitudinal + tensionMouvementLateral + tensionMouvementPivot
            tensionAvantGauche = tensionMouvementLongitudinal - tensionMouvementLateral - tensionMouvementPivot
            # Saturations min et max
            tensionArriereDroit = max(min(pmax, tensionArriereDroit), pmin)
            tensionArriereGauche = max(min(pmax, tensionArriereGauche), pmin)
            tensionAvantDroit = max(min(pmax, tensionAvantDroit), pmin)
            tensionAvantGauche = max(min(pmax, tensionAvantGauche), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 2, "p1": ' + str(tensionArriereDroit) + ', "p2": ' + str(tensionArriereGauche) + ', "p3": ' + str(tensionAvantDroit) + ', "p4": ' + str(tensionAvantGauche) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 2, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
            
            
    def VitesseMoteurArriereDroit(self, vitesse, duree = -1):
        pmin = -20
        pmax = 20
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(vitesse))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 1, "p1": ' + str(p1) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 1, "p1": 0}')
            
            
    def VitesseMoteurArriereGauche(self, vitesse, duree = -1):
        pmin = -20
        pmax = 20
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p2 = eval(str(vitesse))
            # Saturations min et max
            p2 = max(min(pmax, p2), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 1, "p2": ' + str(p2) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 1, "p2": 0}')
            
            
    def VitesseMoteurAvantDroit(self, vitesse, duree = -1):
        pmin = -20
        pmax = 20
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p3 = eval(str(vitesse))
            # Saturations min et max
            p3 = max(min(pmax, p3), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 1, "p3": ' + str(p3) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 1, "p3": 0}')
            
            
    def VitesseMoteurAvantGauche(self, vitesse, duree = -1):
        pmin = -20
        pmax = 20
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p4 = eval(str(vitesse))
            # Saturations min et max
            p4 = max(min(pmax, p4), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 1, "p4": ' + str(p4) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 1, "p4": 0}')
            
            
    def VitesseMoteurs(self, vitesseArriereDroit, vitesseArriereGauche, vitesseAvantDroit, vitesseAvantGauche, duree = -1):
        pmin = -20
        pmax = 20
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(vitesseArriereDroit))
            p2 = eval(str(vitesseArriereGauche))
            p3 = eval(str(vitesseAvantDroit))
            p4 = eval(str(vitesseAvantGauche))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            p2 = max(min(pmax, p2), pmin)
            p3 = max(min(pmax, p3), pmin)
            p4 = max(min(pmax, p4), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 1, "p1": ' + str(p1) + ', "p2": ' + str(p2) + ', "p3": ' + str(p3) + ', "p4": ' + str(p4) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 1, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
            
            
    def VitesseMoteursMouvementLongitudinal(self, vitesse, duree = -1):
        pmin = -20
        pmax = 20
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(vitesse))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 1, "p1": ' + str(p1) + ', "p2": ' + str(p1) + ', "p3": ' + str(p1) + ', "p4": ' + str(p1) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 1, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
            
            
    def VitesseMoteursMouvementLateral(self, vitesse, duree = -1):
        pmin = -20
        pmax = 20
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(vitesse))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 1, "p1": ' + str(-p1) + ', "p2": ' + str(p1) + ', "p3": ' + str(p1) + ', "p4": ' + str(-p1) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 1, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
            
            
    def VitesseMoteursMouvementPivot(self, vitesse, duree = -1):
        pmin = -20
        pmax = 20
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(vitesse))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 1, "p1": ' + str(p1) + ', "p2": ' + str(-p1) + ', "p3": ' + str(p1) + ', "p4": ' + str(-p1) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 1, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
            
            
    def VitesseMoteursMouvement(self, vitesseMoteurMouvementLongitudinal, vitesseMoteurMouvementLateral, vitesseMoteurMouvementPivot, duree = -1):
        pmin = -20
        pmax = 20
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(vitesseMoteurMouvementLongitudinal))
            p2 = eval(str(vitesseMoteurMouvementLateral))
            p3 = eval(str(vitesseMoteurMouvementPivot))
            vitesseArriereDroit = vitesseMoteurMouvementLongitudinal - vitesseMoteurMouvementLateral + vitesseMoteurMouvementPivot
            vitesseArriereGauche = vitesseMoteurMouvementLongitudinal + vitesseMoteurMouvementLateral - vitesseMoteurMouvementPivot
            vitesseAvantDroit = vitesseMoteurMouvementLongitudinal + vitesseMoteurMouvementLateral + vitesseMoteurMouvementPivot
            vitesseAvantGauche = vitesseMoteurMouvementLongitudinal - vitesseMoteurMouvementLateral - vitesseMoteurMouvementPivot
            # Saturations min et max
            vitesseArriereDroit = max(min(pmax, vitesseArriereDroit), pmin)
            vitesseArriereGauche = max(min(pmax, vitesseArriereGauche), pmin)
            vitesseAvantDroit = max(min(pmax, vitesseAvantDroit), pmin)
            vitesseAvantGauche = max(min(pmax, vitesseAvantGauche), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 1, "p1": ' + str(vitesseArriereDroit) + ', "p2": ' + str(vitesseArriereGauche) + ', "p3": ' + str(vitesseAvantDroit) + ', "p4": ' + str(vitesseAvantGauche) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 1, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
            
            
    def AvancerLongitudinal(self, vitesseLongitudinale, duree = -1):
        pmin = -0.5
        pmax = 0.5
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(vitesseLongitudinale))
            # Saturations min et max
            p1 = max(min(pmax, p1), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 0, "p1": ' + str(p1) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 0, "p1": 0}')
    
    
    def AvancerLateral(self, vitesseLaterale, duree = -1):
        pmin = -0.5
        pmax = 0.5
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p2 = eval(str(vitesseLaterale))
            # Saturations min et max
            p2 = max(min(pmax, p2), pmin)
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 0, "p2": ' + str(p2) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 0, "p2": 0}')
    
    
    def Pivoter(self, vitesseRotation, source_ximes, duree = -1):
        pmin = -360
        pmax = 360
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p3 = eval(str(vitesseRotation))
            p4 = eval(str(source_ximes))
            # Saturations min et max
            p3 = max(min(pmax, p3), pmin)
            # p4 vaut 0 ou 1
            if p4 != 0 and p4 != 1:
                p4 = 0
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 0, "p3": ' + str(p3) + ', "p4": ' + str(p4) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 0, "p3": 0, "p4": 0}')
    
    
    def Mouvement(self, vitesseLongitudinale, vitesseLaterale, vitesseRotation, source_ximes, duree = -1):
        p1min = -0.5
        p1max = 0.5
        p2min = -0.5
        p2max = 0.5
        p3min = -360
        p3max = 360
        tdebut = time.time()
        t = time.time() - tdebut
        while t <= duree or duree == -1:
            p1 = eval(str(vitesseLongitudinale))
            p2 = eval(str(vitesseLaterale))
            p3 = eval(str(vitesseRotation))
            p4 = eval(str(source_ximes))
            # Saturations min et max
            p1 = max(min(p1max, p1), p1min)
            p2 = max(min(p2max, p2), p2min)
            p3 = max(min(p3max, p3), p3min)
            # p4 vaut 0 ou 1
            if p4 != 0 and p4 != 1:
                p4 = 0
            # Envoi de la consigne au programme principal par Websocket
            self.ws.send('{"mode": 0, "p1": ' + str(p1) + ', "p2": ' + str(p2) + ', "p3": ' + str(p3) + ', "p4": ' + str(p4) + '}')
            time.sleep(0.1)
            t = time.time() - tdebut
            
            if duree == -1:
                break
        
        if duree != -1:
            self.ws.send('{"mode": 0, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
    
        
   
    def InitialiserPsi(self, valeur):
        self.ws.send('{"mode": 3, "p1": ' + str(valeur) + '}')
        
   
    def LireVariable(self, variable):
        jsonMessage = json.loads(self.message)
        if jsonMessage.get(variable) != None:
            return float(jsonMessage.get(variable))
        else:
            return None
        
   
    def Terminer(self):
        self.started = False
        self.ws.send('{"mode": 0, "p1": 0, "p2": 0, "p3": 0, "p4": 0}')
        self.ws.close()
        
