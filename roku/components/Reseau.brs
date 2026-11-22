' action « jumeler » (valeur = code), « liste », « police » (valeur = adresse du fichier), « oublier ».
' Le jeton reçu au jumelage est gardé dans la mémoire de la TV (section « ameux »), jamais affiché.

sub init()
    m.top.functionName = "executer"
end sub

sub executer()
    action = m.top.action
    if action = "jumeler"
        m.top.resultat = jumeler(m.top.valeur)
    else if action = "liste"
        m.top.resultat = liste()
    else if action = "police"
        m.top.resultat = police(m.top.valeur)
    else if action = "oublier"
        reg = CreateObject("roRegistrySection", "ameux")
        reg.Delete("jeton")
        reg.Flush()
        m.top.resultat = { ok: true }
    end if
end sub

function lireJeton() as String
    reg = CreateObject("roRegistrySection", "ameux")
    if reg.Exists("jeton") then return reg.Read("jeton")
    return ""
end function

function nouvelleRequete(adresse as String) as Object
    u = CreateObject("roUrlTransfer")
    u.SetUrl(adresse)
    u.SetCertificatesFile("common:/certs/ca-bundle.crt")
    u.InitClientCertificates()
    u.EnableEncodings(true)
    u.RetainBodyOnError(true)
    port = CreateObject("roMessagePort")
    u.SetMessagePort(port)
    return { u: u, port: port }
end function

' Attend la réponse (20 s au plus). code 0 = pas de réponse.
function attendre(r as Object, lancee as Boolean) as Object
    if not lancee then return { code: 0, corps: "" }
    msg = wait(20000, r.port)
    if type(msg) = "roUrlEvent" then return { code: msg.GetResponseCode(), corps: msg.GetString() }
    r.u.AsyncCancel()
    return { code: 0, corps: "" }
end function

function lireJson(texte as String) as Dynamic
    if texte = invalid or Len(texte) = 0 then return invalid
    return ParseJson(texte)
end function

function jumeler(code as String) as Object
    r = nouvelleRequete(FLUX_URL() + "/api/affichage/jumeler")
    r.u.AddHeader("Content-Type", "application/json")
    rep = attendre(r, r.u.AsyncPostFromString(FormatJson({ code: code })))
    data = lireJson(rep.corps)
    if rep.code = 200 and data <> invalid and data.jeton <> invalid
        reg = CreateObject("roRegistrySection", "ameux")
        reg.Write("jeton", data.jeton)
        reg.Flush()
        return { ok: true }
    end if
    if data <> invalid and data.error <> invalid then return { ok: false, erreur: data.error }
    return { ok: false, erreur: "AMÉUX Flux ne répond pas. Vérifie la connexion Internet de la TV." }
end function

function liste() as Object
    jeton = lireJeton()
    if jeton = "" then return { ok: false, nonJumele: true }
    r = nouvelleRequete(FLUX_URL() + "/api/roku")
    r.u.AddHeader("Authorization", "Bearer " + jeton)
    rep = attendre(r, r.u.AsyncGetToString())
    if rep.code = 401 then return { ok: false, nonJumele: true }
    data = lireJson(rep.corps)
    if rep.code = 200 and data <> invalid then return { ok: true, liste: data }
    return { ok: false }
end function

' Police Satoshi (Fontshare) copiée dans la mémoire temporaire de la TV, pour l'heure et les bandeaux.
function police(adresse as String) as Object
    fichier = "tmp:/satoshi-noir.ttf"
    if CreateObject("roFileSystem").Exists(fichier) then return { ok: true, fichier: fichier }
    r = nouvelleRequete(adresse)
    rep = attendre(r, r.u.AsyncGetToFile(fichier))
    if rep.code = 200 then return { ok: true, fichier: fichier }
    return { ok: false }
end function
