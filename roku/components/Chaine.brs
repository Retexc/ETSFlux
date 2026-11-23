sub init()
    m.ecran = m.top.findNode("ecran")
    m.avis = m.top.findNode("avis")
    m.texteAvis = m.top.findNode("texteAvis")
    m.finAvis = m.top.findNode("finAvis")
    m.finAvis.observeField("fire", "cacherAvis")
    m.ecran.observeField("etat", "etatEcran")
    m.top.setFocus(true)
end sub

sub etatEcran()
    if m.ecran.etat = "nonJumele" and m.dialogue = invalid then demanderCode("")
end sub

' Fenêtre du code (clavier de la Roku)
sub demanderCode(erreur as String)
    d = CreateObject("roSGNode", "StandardKeyboardDialog")
    standard = d <> invalid
    if not standard then d = CreateObject("roSGNode", "KeyboardDialog")
    d.title = "Connecter cet écran"
    lignes = ["Dans AMÉUX Flux : Annonces → Écran du salon → Connecter un écran.", "Entre le code affiché (ex. : ABCD-2345)."]
    if erreur <> "" then lignes = [erreur, "Entre de nouveau le code d'AMÉUX Flux."]
    if standard
        d.message = lignes
    else
        d.message = lignes[0] + " " + lignes[1]
    end if
    d.buttons = ["Connecter", "Annuler"]
    d.observeField("buttonSelected", "boutonCode")
    m.dialogue = d
    m.top.dialog = d
end sub

sub boutonCode()
    d = m.dialogue
    choix = d.buttonSelected
    code = d.text
    d.close = true
    m.dialogue = invalid
    if choix <> 0 then return
    montrerAvis("Connexion…", 0)
    t = CreateObject("roSGNode", "Reseau")
    t.action = "jumeler"
    t.valeur = code
    t.observeField("resultat", "jumelageFini")
    t.control = "RUN"
    m.tache = t
end sub

sub jumelageFini(evt as Object)
    r = evt.getData()
    if r <> invalid and type(r.ok) = "roBoolean" and r.ok
        montrerAvis("Écran connecté. Pour l'économiseur : Paramètres → Thème → Économiseurs d'écran → AMÉUX.", 12)
        m.ecran.relire = true
    else
        cacherAvis()
        message = "Code refusé."
        if r <> invalid and r.erreur <> invalid then message = r.erreur
        demanderCode(message)
    end if
end sub

sub oublierEtReconnecter()
    t = CreateObject("roSGNode", "Reseau")
    t.action = "oublier"
    t.observeField("resultat", "oubli")
    t.control = "RUN"
    m.tache = t
end sub

sub oubli()
    demanderCode("")
end sub

sub montrerAvis(t as String, secondes as Integer)
    m.texteAvis.text = t
    m.avis.visible = true
    m.finAvis.control = "stop"
    if secondes > 0
        m.finAvis.duration = secondes
        m.finAvis.control = "start"
    end if
end sub

sub cacherAvis()
    m.avis.visible = false
end sub

function onKeyEvent(touche as String, appuyee as Boolean) as Boolean
    if not appuyee then return false
    if touche = "options"
        oublierEtReconnecter()
        return true
    end if
    return false   ' Retour : la Roku ferme la chaîne
end function
