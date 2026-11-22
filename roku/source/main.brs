' AMÉUX : écran du salon étudiant sur la TV Roku.
' - Économiseur d'écran (Paramètres → Thème → Économiseurs d'écran → AMÉUX) : passe les annonces de
'   AMÉUX Flux quand la TV est inactive ; n'importe quelle touche le ferme (Roku s'en charge).
' - Chaîne « AMÉUX » : sert à connecter la TV avec le code de AMÉUX Flux, puis montre l'écran.

sub Main(args as Dynamic)
    afficher("Chaine")
end sub

sub RunScreenSaver()
    afficher("Economiseur")
end sub

sub afficher(nomScene as String)
    ecran = CreateObject("roSGScreen")
    port = CreateObject("roMessagePort")
    ecran.SetMessagePort(port)
    ecran.CreateScene(nomScene)
    ecran.Show()
    while true
        msg = wait(0, port)
        if type(msg) = "roSGScreenEvent" and msg.IsScreenClosed() then return
    end while
end sub
