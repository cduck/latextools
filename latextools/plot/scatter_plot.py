import string

from .. import str_util
from .. import (
    LatexPackage,
    CommandBundle,
    LatexContentAbc,
    PlainTextFile,
    INDENT_STEP,
)


tikz = LatexPackage('tikz', setup_content=
        '\n'.join(fr'\usetikzlibrary{{{u}}}'
                  for u in ['patterns', 'arrows', 'external']))
pgfplots = LatexPackage('pgfplots', packages=[tikz], setup_content=
        r'\pgfplotsset{{compat=1.14}}')

plot_deps = CommandBundle(
        packages=[
            tikz,
            pgfplots,
        ])


FILE_TEMPLATE = r'''\begin{{tikzpicture}}[baseline,scale={scale},trim axis left,trim axis right]
%\pgfplotsset{{every axis/.append style={{thick}}}}
\pgfplotsset{{every tick label/.append style={{font=\small}}}}
\pgfplotsset{{every axis label/.append style={{font=\small}}}}

{plots}

\end{{tikzpicture}}
'''

PLOT_TEMPLATE = r'''\begin{{axis}}[
    name={name},
    title={{{title}}},
    xlabel={{{xlabel}}},
    ylabel={{{ylabel}}},
    width={{{width}}},
    height={{{height}}},
%    xmin=0, xmax=0,
%    ymin=0,
%    restrict x to domain=0:0,
%    xtick distance=25,
    ,
    legend style={{
        draw=none,{legend_options}
%        fill=none,
        font=\small}},
%    legend columns=-1,
    {legend_horizontal},
    clip=false,{options}
]

{graphs}
\end{{axis}}'''

GRAPH_TEMPLATE = r'''\addplot[color={color}] table[x={x_col}, y={y_col}, col sep=comma]
    {{{data_path}}}
;%node [anchor=north east] {{...}};{legend_entry}'''


def clean_string(s):
    if s is None:
        return ''
    allowed_chars = string.ascii_letters + string.digits + '-'
    return ''.join(c for c in s.replace(' ', '-').lower()
                     if c in allowed_chars)

def escape_latex(s):
    return s.replace('_', r'\_')


class PgfplotsFigure(LatexContentAbc):
    def __init__(self, scale=1):
        super().__init__([], [plot_deps], 'Pgfplots figure')
        self.scale = scale
        self.plot_list = []

    def append_plot(self, plot):
        self.plot_list.append(plot)

    def add_subplot(self, num_rows=1, num_cols=1, i1=1):
        plot = Plot()
        self.append_plot(plot)
        return plot

    def _latex_code_body(self, indent=''):
        plots_str = '\n\n'.join(p._latex_code_body(
                                    indent=INDENT_STEP, i=i)
                                for i, p in enumerate(self.plot_list))
        out = FILE_TEMPLATE.format(plots=plots_str, scale=self.scale)
        return str_util.prefix_lines(indent, out)

    def list_sub_content(self):
        return self.plot_list


class Plot(LatexContentAbc):
    GRAPH_TYPE = None

    def __init__(self, title='', xlabel='', ylabel='',
                 width='\columnwidth', height='0.6\columnwidth',
                 hide_box=False, hide_x_tick_labels=False,
                 hide_y_tick_labels=False, legend_pos='top-left',
                 legend_at=None, legend_horizontal=False):
        super().__init__([], [plot_deps], 'Pgfplots plot')
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.width = width
        self.height = height
        self.hide_box = hide_box
        self.hide_x_tick_labels = hide_x_tick_labels
        self.hide_y_tick_labels = hide_y_tick_labels
        self.legend_pos = legend_pos
        self.legend_at = legend_at
        self.legend_horizontal = legend_horizontal
        self.graph_list = []
        self.data_file = None

    def append_graph(self, graph):
        self.graph_list.append(graph)

    def plot(self, x_data, y_data, fmt='', **kwargs):
        graph = self.GRAPH_TYPE(x_data, y_data, fmt=fmt, **kwargs)
        self.append_graph(graph)
        return graph

    def legend(self, legend):
        for g, l in zip(self.graph_list, legend):
            g.legend = l

    def set_title(self, title):
        self.title = title

    def set_xlabel(self, xlabel):
        self.xlabel = xlabel

    def set_ylabel(self, ylabel):
        self.ylabel = ylabel

    def get_clean_name(self):
        return clean_string(self.title)

    def get_data_path(self):
        name = self.get_clean_name()
        return f'data/{name}.csv'

    def _get_x_col(self, i, g):
        return f'{clean_string(self.xlabel) or "x"} {i}'

    def _get_y_col(self, i, g):
        return (f'{clean_string(g.legend)} {clean_string(self.ylabel)} {i}'
                .strip())

    def _is_x_common(self):
        return all(self.graph_list[0].x_data == g.x_data
                   for g in self.graph_list)

    def _latex_code_body(self, indent='', i=0):
        is_x_common = self._is_x_common()
        x_col_common = clean_string(self.xlabel) or 'x' if is_x_common else None
        graphs_str = ''
        for i, g in enumerate(self.graph_list):
            x_col = x_col_common or self._get_x_col(i, g)
            graphs_str += g._latex_code_body(
                                indent=INDENT_STEP,
                                x_col=x_col,
                                y_col=self._get_y_col(i, g),
                                legend_horizontal=self.legend_horizontal,
                                last=i >= len(self.graph_list)-1,
                                data_path=self.get_data_path())
            graphs_str += '\n\n'
        option_list = []
        if self.hide_box:
            option_list.append(r'axis line style={draw=none}')
            option_list.append(r'tick style={draw=none}')
        if self.hide_x_tick_labels:
            option_list.append(r'xticklabels={}')
        if self.hide_y_tick_labels:
            option_list.append(r'yticklabels={}')
        options_str = ',\n    '.join(option_list)
        if option_list:
            options_str = '\n    '+options_str+','
        legend_option_list = []
        if self.legend_pos == 'center':
            at_str = '(0.5,0.5)'
            anchor = 'center'
        elif self.legend_pos == 'top-left':
            at_str = '(0,1)'
            anchor = 'north west'
        elif self.legend_pos == 'top':
            at_str = '(0.5,1)'
            anchor = 'north'
        elif self.legend_pos == 'top-right':
            at_str = '(1,1)'
            anchor = 'north east'
        elif self.legend_pos == 'right':
            at_str = '(1,0.5)'
            anchor = 'east'
        elif self.legend_pos == 'bottom-right':
            at_str = '(1,0)'
            anchor = 'south east'
        elif self.legend_pos == 'bottom':
            at_str = '(0.5,0)'
            anchor = 'south'
        elif self.legend_pos == 'bottom-left':
            at_str = '(0,0)'
            anchor = 'south west'
        elif self.legend_pos == 'left':
            at_str = '(0,0.5)'
            anchor = 'west'
        if self.legend_at is not None:
            if isinstance(self.legend_at, str):
                at_str = self.legend_at
            else:
                at_str = f'({self.legend_at[0]},{self.legend_at[1]})'
        legend_option_list.append(fr'at={{{at_str}}}')
        legend_option_list.append(f'anchor={anchor}')
        legend_options_str = ',\n        '.join(legend_option_list)
        if legend_option_list:
            legend_options_str = '\n        '+legend_options_str+','
        if self.legend_horizontal:
            legend_horizontal_str = 'legend columns=-1'
        else:
            legend_horizontal_str = ''
        out = PLOT_TEMPLATE.format(graphs=graphs_str,
                                   title=escape_latex(self.title),
                                   name=f'plot{i}',
                                   xlabel=escape_latex(self.xlabel),
                                   ylabel=escape_latex(self.ylabel),
                                   width=self.width,
                                   height=self.height,
                                   options=options_str,
                                   legend_options=legend_options_str,
                                   legend_horizontal=legend_horizontal_str)
        return str_util.prefix_lines(indent, out)

    def get_required_files(self):
        if self.data_file is None:
            self._init_data_file()
        return [self.data_file]

    def _init_data_file(self):
        file_content = self._data_file_content()
        self.data_file = PlainTextFile(self.get_data_path(), file_content)

    def _data_file_content(self):
        column_names = []
        columns = []

        is_x_common = self._is_x_common()
        if is_x_common:
            common_x_data = self.graph_list[0].x_data
            column_names.append(clean_string(self.xlabel) or 'x')
            columns.append(common_x_data)

        for i, g in enumerate(self.graph_list):
            if not is_x_common:
                column_names.append(self._get_x_col(i, g))
                columns.append(g.x_data)
            column_names.append(self._get_y_col(i, g))
            columns.append(g.y_data)

        out = ''
        out += ','.join(column_names)
        out += '\n'
        for row_i in range(max(map(len, columns))):
            out += ','.join(str(col[row_i]) if row_i < len(col) else ''
                                            for col in columns)
            out += '\n'
        return out


class Graph(LatexContentAbc):
    def __init__(self, x_data, y_data, fmt='', legend='', color='black',
                 **kwargs):
        super().__init__([], [plot_deps], 'Pgfplots graph')
        self.x_data = x_data
        self.y_data = y_data
        self.fmt = fmt
        self.legend = legend
        self.color = color

    def _latex_code_body(self, indent='', x_col='x', y_col='y',
                         legend_horizontal=False, last=False,
                         data_path='data/data.csv'):
        if self.legend is None:
            legend_entry = ''
        else:
            legend = self.legend
            if legend_horizontal and not last:
                legend += '~~~~'
            legend_entry = ('\n'
                            fr'\addlegendentry{{{escape_latex(legend)}}};')
        out = GRAPH_TEMPLATE.format(x_col=x_col, y_col=y_col,
                                    legend_entry=legend_entry,
                                    color=self.color,
                                    data_path=data_path)
        return str_util.prefix_lines(indent, out)

Plot.GRAPH_TYPE = Graph
