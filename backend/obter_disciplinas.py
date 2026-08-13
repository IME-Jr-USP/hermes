import jupiterweb

institutos_usp = jupiterweb.obter_institutos()
instituto = institutos_usp[37] # por enquanto estamos pegando apenas as disciplinas do IME (cod 37)

disciplinas_instituto = instituto.obter_disciplinas()