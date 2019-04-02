from .. import INDENT_STEP, str_util
from .scatter_plot import Plot, Graph, clean_string, escape_latex


BAR_PLOT_TEMPLATE = r'''\begin{{axis}}[
    name={name},
    title={{{title}}},
    xlabel={{{xlabel}}},
    ylabel={{{ylabel}}},
    symbolic x coords={{{x_coords}}},
    width=\columnwidth + 20pt,
    height=150pt,
    ybar=5pt,
    bar width=15pt,
    enlargelimits={enlargelimits},
    ymin={ymin}, ymax={ymax},
%    ytick={{0, 25, 50, 75, 100}},
%    ytick distance=25,
    xtick=data,
    ,
    legend style={{draw=none, fill=none, at={{(0.5,1.03)}},anchor=north,font=\small}},
    legend columns=-1,
    legend image code/.code={{\draw[#1, draw=none] (0em,-0.2em) rectangle (0.6em,0.4em);}},
    axis line style={{draw=black!20!white}},
    axis on top,
    y axis line style={{draw=none}},
    axis x line*=bottom,
    tick style={{draw=none}},
    yticklabel={{\pgfmathparse{{\tick*1}}\pgfmathprintnumber{{\pgfmathresult}}{y_tick_suffix}}},
    clip=false,
    enlarge y limits=0,
    ,
    % From: https://tex.stackexchange.com/questions/449620/editing-label-on-bar-chart
    nodes near coords always on top/.style={{
        % a new feature since 1.9: allows to place markers absolutely:
%        scatter/position=absolute,
        every node near coord/.append style={{
%            at={{(axis cs:\pgfkeysvalueof{{/data point/x}},\pgfkeysvalueof{{/data point/y}})}},
%            draw,      % <-- for debugging only, to check if placement is correct
            anchor=south,
            rotate=0,
            font=\small,
            inner sep=0.2em,
        }},
    }},
    nodes near coords always on top,
]

{graphs}

\end{{axis}}'''

BAR_GRAPH_TEMPLATE = r'''\addplot[style={{color=transparent, draw=none, fill={color}, mark=none}}] coordinates {{
    {data}
}};
\addlegendentry{{{legend}}};'''


class BarPlot(Plot):
    def __init__(self, title='', xlabel='', ylabel='', y_tick_suffix=r'\%'):
        super().__init__(title=title, xlabel=xlabel, ylabel=ylabel)
        self.y_tick_suffix = y_tick_suffix

    def bar(self, x_data, y_data, fmt='', **kwargs):
        return super().plot(x_data, y_data, fmt=fmt, **kwargs)

    def get_data_path(self):
        return None

    def _latex_code_body(self, indent='', i=0):
        x_coords = ','.join(map(escape_latex,
                                map(str, self.graph_list[0].x_data)))
        enlargelimits = (1 if len(self.graph_list[0].x_data) <= 1
                         else 1/2/(len(self.graph_list[0].x_data)-1))
        ymin = 0
        ymax = max(max(g.y_data) for g in self.graph_list)
        ymax *= 8/7
        graphs_str = '\n\n'.join(g._latex_code_body(
                                    indent=INDENT_STEP,
                                    last=i >= len(self.graph_list)-1)
                                 for i, g in enumerate(self.graph_list))
        out = BAR_PLOT_TEMPLATE.format(x_coords=x_coords,
                                       enlargelimits=enlargelimits,
                                       ymin=ymin, ymax=ymax,
                                       graphs=graphs_str,
                                       title=escape_latex(self.title),
                                       name=f'plot{i}',
                                       xlabel=escape_latex(self.xlabel),
                                       ylabel=escape_latex(self.ylabel),
                                       y_tick_suffix=self.y_tick_suffix)
        return str_util.prefix_lines(indent, out)

    def get_required_files(self):
        return ()

    def write_data(self):
        return


class BarGraph(Graph):
    def __init__(self, x_data, y_data, fmt='', legend='', color='black',
                 **kwargs):
        super().__init__(x_data, y_data, fmt=fmt, legend=legend, color=color,
                         **kwargs)

    def _latex_code_body(self, indent='', x_col=None, y_col=None,
                         data_path=None, last=False):
        legend = escape_latex(self.legend) + '~~~~'*(not last)
        data_str = '\n    '.join(f'({escape_latex(str(x))}, {y})'
                                 for x, y in zip(self.x_data, self.y_data))
        out = BAR_GRAPH_TEMPLATE.format(legend=legend,
                                        color=self.color,
                                        data=data_str)
        return str_util.prefix_lines(indent, out)

BarPlot.GRAPH_TYPE = BarGraph
