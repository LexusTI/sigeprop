def verificar_campos_vazios(*args):
    for arg in args:
        if arg==None:
            return 'Campos vazios'
        if arg.strip=='':
            return 'Campos vazios'
        
    return False
def verificar_senha(senha):
    if senha!=None:
        if len(senha)<8:
            return 'Senha menor que 8 caracteres!'
        if senha.isnumeric():
            return 'Senha não pode ser totalmente numérica!'
        if senha.isalpha():
            return 'Senha deve conter números!'
    else:
        return 'Senha menor que 8 caracteres!'
    return False
