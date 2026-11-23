sub init()
    for each id in ["afficheA", "afficheB", "prechargement", "fondVideo", "video", "entete", "heure", "notice", "bandeauAlertes", "texteAlertes", "bandeauMessages", "texteMessages", "message", "minuterieDiapo", "minuterieLecture", "minuterieHeure", "minuterieNotice", "finNotice", "gardeVideo"]
        m[id] = m.top.findNode(id)
    end for
    m.affichee = m.afficheA          ' affiche à l'écran ; l'autre charge la prochaine image
    m.diapos = []
    m.index = -1
    m.version = ""
    m.textes = { messages: "", alertes: "" }
    m.fichierPolice = ""
    m.polices = {}
    m.minuterieDiapo.observeField("fire", "suivante")
    m.minuterieLecture.observeField("fire", "lire")
    m.minuterieHeure.observeField("fire", "majHeure")
    m.minuterieNotice.observeField("fire", "montrerNotice")
    m.finNotice.observeField("fire", "cacherNotice")
    m.video.observeField("state", "etatVideo")
    m.video.mute = true                  ' sans son, comme l'écran web (et un économiseur ne doit pas jouer de son)
    m.gardeVideo.observeField("fire", "videoBloquee")
    m.afficheA.observeField("loadStatus", "imageChargee")
    m.afficheB.observeField("loadStatus", "imageChargee")
    appliquerPolices()
    m.minuterieLecture.control = "start"
    m.minuterieHeure.control = "start"
    m.minuterieNotice.control = "start"
    lire()
end sub

' ---------- Liste (AMÉUX Flux, chaque minute) ----------

sub lire()
    t = CreateObject("roSGNode", "Reseau")
    t.action = "liste"
    t.observeField("resultat", "listeRecue")
    t.control = "RUN"
    m.tacheListe = t
end sub

sub listeRecue(evt as Object)
    r = evt.getData()
    if r = invalid then return
    if vrai(r.nonJumele)
        m.top.etat = "nonJumele"
        arreterTout()
        afficherMessage("Cet écran n'est pas encore connecté." + Chr(10) + "Ouvre la chaîne AMÉUX pour entrer le code d'AMÉUX Flux.")
        return
    end if
    if not vrai(r.ok)
        ' Flux ou Internet en panne : la dernière liste reste affichée
        if m.diapos.Count() = 0 then afficherMessage("AMÉUX Flux ne répond pas. Nouvel essai dans une minute.")
        return
    end if
    l = r.liste
    m.top.etat = "ok"
    if m.fichierPolice = "" and l.police <> invalid and l.police <> "" then chargerPolice(l.police)
    if l.notice <> invalid then m.notice.uri = l.notice
    m.textes = { messages: texte(l.messages), alertes: texte(l.alertes) }
    if l.version = m.version then return
    m.version = l.version

    idActuel = invalid
    if m.index >= 0 and m.index < m.diapos.Count() then idActuel = m.diapos[m.index].id
    m.diapos = []
    if l.diapos <> invalid then m.diapos = l.diapos
    if m.diapos.Count() = 0
        arreterTout()
        afficherMessage("Rien à l'écran pour l'instant.")
        return
    end if
    cacherMessage()

    ' Même diapositive encore là : son image est mise à jour sans recommencer son temps
    m.index = -1
    for i = 0 to m.diapos.Count() - 1
        if m.diapos[i].id = idActuel then m.index = i
    end for
    if m.index >= 0
        d = m.diapos[m.index]
        if d.sorte = "image" then afficherImage(d.image)
        majBas(d)
    else
        suivante()
    end if
end sub

function texte(v as Dynamic) as String
    if v = invalid then return ""
    return v
end function

' ---------- Diapositives ----------

sub suivante()
    n = m.diapos.Count()
    if n = 0 then return
    m.index = (m.index + 1) mod n
    montrer(m.diapos[m.index])
    ' La suivante se charge déjà (sans s'afficher) : pas d'attente au changement
    prochaine = m.diapos[(m.index + 1) mod n]
    if prochaine.sorte = "image" and prochaine.image <> invalid then m.prechargement.uri = prochaine.image
end sub

sub montrer(d as Object)
    m.minuterieDiapo.control = "stop"
    if d.sorte = "video"
        contenu = CreateObject("roSGNode", "ContentNode")
        contenu.url = d.video
        contenu.streamFormat = "mp4"
        m.video.control = "stop"
        m.video.content = contenu
        m.fondVideo.visible = true
        m.video.visible = true
        m.entete.uri = d.image
        m.entete.visible = true
        print "[ameux] vidéo : "; d.video
        m.video.control = "play"
        m.gardeVideo.control = "start"   ' pas démarrée dans 20 s : on passe à la suivante
        if d.duree_s > 0
            programmer(d.duree_s)
        else
            programmer(600)               ' « jusqu'à la fin » : 10 min au plus, comme l'écran web
        end if
    else
        arreterVideo()
        afficherImage(d.image)
        programmer(d.duree_s)
    end if
    if not vrai(d.notice) then cacherNotice()
    majBas(d)
    majHeure()
end sub

sub programmer(secondes as Dynamic)
    if secondes = invalid or secondes < 3 then secondes = 10
    m.minuterieDiapo.duration = secondes
    m.minuterieDiapo.control = "start"
end sub

sub etatVideo()
    etat = m.video.state
    print "[ameux] état de la vidéo : "; etat; " "; m.video.errorCode; " "; m.video.errorMsg
    if etat = "playing" then m.gardeVideo.control = "stop"
    if m.index < 0 or m.index >= m.diapos.Count() then return
    d = m.diapos[m.index]
    if d.sorte <> "video" then return
    if etat = "finished" and d.duree_s = 0 then suivante()
    if etat = "error" then suivante()   ' vidéo illisible : on passe à la suivante
end sub

sub videoBloquee()
    print "[ameux] la vidéo n'a pas démarré : suivante"
    suivante()
end sub

sub arreterVideo()
    m.gardeVideo.control = "stop"
    if m.video.visible then m.video.control = "stop"
    m.video.visible = false
    m.fondVideo.visible = false
    m.entete.visible = false
end sub

sub arreterTout()
    m.minuterieDiapo.control = "stop"
    arreterVideo()
    m.afficheA.visible = false
    m.afficheB.visible = false
    m.heure.visible = false
    m.bandeauMessages.visible = false
    m.bandeauAlertes.visible = false
    cacherNotice()
    m.index = -1
    m.version = ""
end sub

' L'image se charge dans l'affiche cachée, puis remplace celle à l'écran (jamais d'écran vide).
sub afficherImage(adresse as Dynamic)
    if adresse = invalid or adresse = "" then return
    if m.affichee.uri = adresse and m.affichee.visible then return
    cachee = m.afficheA
    if m.affichee.isSameNode(m.afficheA) then cachee = m.afficheB
    m.attendue = adresse
    if cachee.uri = adresse and cachee.loadStatus = "ready"
        echanger(cachee)
    else
        cachee.uri = adresse
    end if
end sub

sub imageChargee(evt as Object)
    affiche = evt.getRoSGNode()
    if affiche.uri <> m.attendue then return
    if affiche.loadStatus = "ready" then echanger(affiche)
end sub

sub echanger(affiche as Object)
    affiche.visible = true
    if not m.affichee.isSameNode(affiche) then m.affichee.visible = false
    m.affichee = affiche
end sub

' ---------- Heure, bandeaux, notice ----------

sub majHeure()
    if m.index < 0 or m.index >= m.diapos.Count() then return
    h = m.diapos[m.index].heure
    if h = invalid
        m.heure.visible = false
        return
    end if
    dt = CreateObject("roDateTime")
    dt.ToLocalTime()
    minutes = dt.GetMinutes().ToStr()
    if Len(minutes) < 2 then minutes = "0" + minutes
    m.heure.text = dt.GetHours().ToStr() + " h " + minutes
    m.heure.color = couleur(h.couleur)
    m.heure.font = police(h.taille)
    m.heure.translation = [1920 - h.droite - 400, h.centreY - 30]
    m.heure.visible = true
end sub

' Bandeau d'annonces (toujours) et alertes STM (diapositives de transport), empilés en bas.
sub majBas(d as Object)
    nombre = 0
    if m.textes.messages <> ""
        if m.texteMessages.text <> m.textes.messages then m.texteMessages.text = m.textes.messages
        m.bandeauMessages.translation = [0, 1080 - 56]
        m.bandeauMessages.visible = true
        nombre = 1
    else
        m.bandeauMessages.visible = false
    end if
    if vrai(d.transport) and m.textes.alertes <> ""
        if m.texteAlertes.text <> m.textes.alertes then m.texteAlertes.text = m.textes.alertes
        m.bandeauAlertes.translation = [0, 1080 - 56 * (nombre + 1)]
        m.bandeauAlertes.visible = true
        nombre = nombre + 1
    else
        m.bandeauAlertes.visible = false
    end if
    m.notice.translation = [0, 1080 - (6 + 56 * nombre) - 34 - 130]
end sub

sub montrerNotice()
    if m.index < 0 or m.index >= m.diapos.Count() then return
    if not vrai(m.diapos[m.index].notice) or m.notice.uri = "" then return
    m.notice.visible = true
    m.finNotice.control = "start"
end sub

sub cacherNotice()
    m.notice.visible = false
end sub

sub afficherMessage(t as String)
    m.message.text = t
    m.message.font = police(34)
    m.message.visible = true
end sub

sub cacherMessage()
    m.message.visible = false
end sub

' ---------- Police (Satoshi, sinon la police de la Roku) ----------

sub chargerPolice(adresse as String)
    t = CreateObject("roSGNode", "Reseau")
    t.action = "police"
    t.valeur = adresse
    t.observeField("resultat", "policeChargee")
    t.control = "RUN"
    m.tachePolice = t
end sub

sub policeChargee(evt as Object)
    r = evt.getData()
    if r = invalid or not vrai(r.ok) then return
    m.fichierPolice = r.fichier
    m.polices = {}
    appliquerPolices()
    majHeure()
end sub

sub appliquerPolices()
    m.texteMessages.font = police(26)
    m.texteAlertes.font = police(26)
    m.message.font = police(34)
end sub

function police(taille as Integer) as Object
    cle = taille.ToStr()
    if m.polices[cle] <> invalid then return m.polices[cle]
    f = CreateObject("roSGNode", "Font")
    if m.fichierPolice <> ""
        f.uri = m.fichierPolice
    else
        f.uri = "font:BoldSystemFontFile"
    end if
    f.size = taille
    m.polices[cle] = f
    return f
end function

' « #RRGGBB » → « 0xRRGGBBFF »
function couleur(c as Dynamic) as String
    if c = invalid or Len(c) <> 7 then return "0xFFFFFFFF"
    return "0x" + Mid(c, 2) + "FF"
end function

' Vrai seulement pour le booléen true (une valeur absente donne faux, sans erreur).
function vrai(v as Dynamic) as Boolean
    if v = invalid then return false
    if type(v) <> "Boolean" and type(v) <> "roBoolean" then return false
    return v
end function
