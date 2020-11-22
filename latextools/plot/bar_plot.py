from .. import INDENT_STEP, str_util
from .scatter_plot import Plot, Graph, clean_string, escape_latex


BAR_PLOT_TEMPLATE = r'''\begin{{{axis}}}[
    name={name},
    title={{{title}}},
    xlabel={{{xlabel}}},
    ylabel={{{ylabel}}},
    symbolic x coords={{{x_coords}}},
    width={{{width}}},
    height={{{height}}},
    ybar={{{bar_space}}},
    bar width={{{bar_width}}},
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
    {yticklabel},
    clip=false,
    enlarge y limits=0,
    ,
    x tick label style={{{x_tick_label_style}}},
    grid=none,
    ymajorgrids={ygrid},
    {extra_config},
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
{extra_graphs}%
\end{{{axis}}}'''

BAR_GRAPH_TEMPLATE = r'''\addplot[
    style={{
        color=transparent,
        draw=none,
        fill={color},
        {pattern},
        mark=none,
        {bar_shift},
        {extra_config},
    }},
    {error_bar_config}]
coordinates {{
    {data}
}};{legend}'''


class BarPlot(Plot):
    def __init__(self, title='', xlabel='', ylabel='', ymin=None, ymax=None,
                 width='\columnwidth', height='0.6\columnwidth',
                 bar_width='15pt', bar_space='5pt', y_tick_suffix=r'',
                 rotate_labels=False, x_sort_key=None, ygrid=False, log=False,
                 extra_config=r'', extra_graphs=r''):
        super().__init__(title=title, xlabel=xlabel, ylabel=ylabel, ymin=ymin,
                         ymax=ymax, width=width, height=height,
                         extra_config=extra_config, extra_graphs=extra_graphs)
        self.bar_width = bar_width
        self.bar_space = bar_space
        self.y_tick_suffix = y_tick_suffix
        self.rotate_labels = rotate_labels
        self.x_sort_key = x_sort_key
        self.ygrid = ygrid
        self.log = log

    def bar(self, x_data, y_data, fmt='', **kwargs):
        return super().plot(x_data, y_data, fmt=fmt, **kwargs)

    def get_data_path(self):
        return None

    def _latex_code_body(self, indent='', i=0):
        axis = 'semilogyaxis' if self.log else 'axis'
        all_x_data = list(self.graph_list[0].x_data)
        for graph in self.graph_list[1:]:
            for x in graph.x_data:
                if x not in all_x_data:
                    all_x_data.append(x)
        if self.x_sort_key is not None:
            all_x_data = sorted(all_x_data, key=self.x_sort_key)
        x_coords = ','.join(map(escape_latex,
                                map(str, all_x_data)))
        enlargelimits = (1 if len(all_x_data) <= 1
                         else 1/2/(len(all_x_data)-1))
        ymin = 0 if self.ymin is None else self.ymin
        if self.ymax is None:
            ymax = max(max(g.y_data) for g in self.graph_list)
            ymax *= 1.3
        else:
            ymax = self.ymax
        graphs_str = '\n\n'.join(g._latex_code_body(
                                    indent=INDENT_STEP,
                                    last=i >= len(self.graph_list)-1,
                                    all_x_data=all_x_data,
                                    x_sort_key=self.x_sort_key)
                                 for i, g in enumerate(self.graph_list))
        if self.rotate_labels:
            if self.rotate_labels == True:
                x_tick_label_style = r'rotate=45, anchor=east'
            else:
                x_tick_label_style = f'rotate={self.rotate_labels}, anchor=east'
        else:
            x_tick_label_style = ''
        if self.y_tick_suffix:
            yticklabel = (
                rf'yticklabel={{\pgfmathparse{{\tick*1}}\pgfmathprintnumber{{'
                rf'\pgfmathresult}}{self.y_tick_suffix}}}')
        else:
            yticklabel = ''
        out = BAR_PLOT_TEMPLATE.format(axis=axis,
                                       x_coords=x_coords,
                                       enlargelimits=enlargelimits,
                                       ymin=ymin, ymax=ymax,
                                       width=self.width, height=self.height,
                                       bar_width=self.bar_width,
                                       bar_space=self.bar_space,
                                       graphs=graphs_str,
                                       title=escape_latex(self.title),
                                       name=f'plot{i}',
                                       xlabel=escape_latex(self.xlabel),
                                       ylabel=escape_latex(self.ylabel),
                                       yticklabel=yticklabel,
                                       x_tick_label_style=x_tick_label_style,
                                       ygrid='true' if self.ygrid else 'false',
                                       extra_config=self.extra_config,
                                       extra_graphs=self.extra_graphs)
        return str_util.prefix_lines(indent, out)

    def get_required_files(self):
        return ()

    def write_data(self):
        return


class BarGraph(Graph):
    def __init__(self, x_data, y_data, fmt='', x_error=None, y_error=None,
                 legend='', color='black',
                 pattern=None, bar_shift=None, extra_config='', **kwargs):
        super().__init__(x_data, y_data, fmt=fmt, x_error=x_error,
                         y_error=y_error, legend=legend, color=color,
                         **kwargs)
        self.pattern = pattern
        self.bar_shift = bar_shift
        self.extra_config = extra_config

    def _latex_code_body(self, indent='', x_col=None, y_col=None,
                         x_err_col=None, y_err_col=None,
                         data_path=None, last=False, all_x_data=(),
                         x_sort_key=None):
        x_data = list(self.x_data)
        y_data = list(self.y_data)
        x_error = ([0]*len(x_data) if self.x_error is None
                                   else list(self.x_error))
        y_error = ([0]*len(y_data) if self.y_error is None
                                   else list(self.y_error))
        for x in all_x_data:
            if x not in x_data:
                x_data.append(x)
                y_data.append(0)
        if x_sort_key is not None:
            x_data, y_data = zip(*sorted(zip(x_data, y_data),
                                 key=lambda xy:x_sort_key(xy[0])))
        if self.legend is not None:
            legend = escape_latex(self.legend) + '~~~~'*(not last)
            legend_str = '\n' fr'\addlegendentry{{{legend}}};'
        else:
            legend_str = ''
        if self.bar_shift:
            bar_shift_str = 'bar shift=' + self.bar_shift
        else:
            bar_shift_str = ''
        if self.pattern is not None:
            pattern_str = 'pattern='+self.pattern
        else:
            pattern_str = ''
        error_bar_config = ''
        if self.x_error is not None or self.y_error is not None:
            error_bar_config += 'error bars/.cd'
            if self.x_error is not None:
                error_bar_config += ',x dir=both,x explicit'
            if self.y_error is not None:
                error_bar_config += ',y dir=both,y explicit'
        data_str = '\n    '.join(
                f'({escape_latex(str(x))}, {y})'
                + (f' +- ({xe}, {ye})' if error_bar_config else '')
                for x, y, xe, ye in zip(x_data, y_data, x_error, y_error))
        out = BAR_GRAPH_TEMPLATE.format(legend=legend_str,
                                        color=self.color,
                                        pattern=pattern_str,
                                        bar_shift=bar_shift_str,
                                        extra_config=self.extra_config,
                                        error_bar_config=error_bar_config,
                                        data=data_str)
        return str_util.prefix_lines(indent, out)

BarPlot.GRAPH_TYPE = BarGraph
