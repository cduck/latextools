from .. import LatexPackage, LatexCommand, CommandBundle, BasicContent


tikz = LatexPackage('tikz', setup_content=
        '\n'.join(fr'\usetikzlibrary{{{u}}}'
                  for u in ['patterns',
                            'arrows',
                            'external',
                            'pgfplots.groupplots']))
pgfplots = LatexPackage('pgfplots', packages=[tikz], setup_content=
        r'\pgfplotsset{{compat=1.14}}')
siunitx = LatexPackage('siunitx', options=['detect-family'])
sansmath = LatexPackage('sansmath', options=['eulergreek'])
relsize = LatexPackage('relsize')

sisetup = LatexCommand('sisetup', r'\sisetup{text-sf=\sansmath}',
        packages=[siunitx, sansmath])

artist_deps = CommandBundle(
        sisetup,
        packages=[
            tikz,
            pgfplots,
            siunitx,
            sansmath,
            relsize,
        ])


class ArtistContent(BasicContent):
    def __init__(self, plot):
        '''
        Wraps a plot object from the Artist plotting python package.

        Args:
            plot: Any artist plot with a render() method
        '''
        code = plot.render()
        super().__init__(code, [], [artist_deps], 'Artist plot')
