import os

class PromptService:
    '''
    Provides an interface to the prompts stored in the repository.
    Includes methods to return static prompts such as the system prompt, 
    and potentially parameterized prompts in the future.
    '''
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    promptsDir = os.path.join(scriptDir, "../../Prompts")

    # TODO: Write Unit Test for this
    def getSystem(self) -> str:
        """
        Returns the base system prompt for the system as a string.
        """
        with open(f'{self.promptsDir}/System.txt') as s:
            content = s.read()
            return content