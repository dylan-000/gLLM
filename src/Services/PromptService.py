import os

class PromptService:
    '''
    Provides methods to retrieve various prompts and create prompt templates.
    '''
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    promptsDir = os.path.join(scriptDir, "../Prompts")

    def getSystem(self) -> str:
        '''
        Returns the default system prompt.
        
        :return: The default system prompt.
        :rtype: str
        '''
        with open(f'{self.promptsDir}/System.txt') as s:
            content = s.read()
            return content