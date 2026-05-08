%% plot_collected_metrics_comparison.m
% =========================================================================
% EMQX Cloud – Parris vs Schultz Side-by-Side Comparison
%              220 tags  |  1100 tags
% =========================================================================
%
% Description:
%   Generates 4 figures (one per metric), each with two subplots:
%     Left  – 220 tags experiment
%     Right – 1100 tags experiment
%
%   Units match the paper:
%     - Messages: messages/sec
%     - Bytes:    Bytes/sec
%
%   Colors match the paper:
%     - Blue  (#0072BD) = Parris Method
%     - Red   (#D95319) = Schultz Method
%
% Input:
%   C:\...\data\processed\collected_metrics_220tags_processed.csv
%   C:\...\data\processed\collected_metrics_1100tags_processed.csv
%
% Author:
%   Juliam Diaz – Master's Thesis, 2025
% =========================================================================

%% Paths
BASE    = 'C:\Users\John Arenas\Desktop\data\uns-performance-evaluation\data\processed\';
csv220  = [BASE 'collected_metrics_220tags_processed.csv'];
csv1100 = [BASE 'collected_metrics_1100tags_processed.csv'];

%% Colors
C_PARRIS  = [0.85, 0.33, 0.10];   % red/orange – Parris Method
C_SCHULTZ = [0.00, 0.45, 0.74];   % blue       – Schultz Method

%% Metric definitions
metricDefs = {
    'Parris_messages_inbound',  'Schultz_messages_inbound',  'Received Message [messages/sec]'
    'Parris_messages_outbound', 'Schultz_messages_outbound', 'Sent Message [messages/sec]'
    'Parris_received_bytes',    'Schultz_received_bytes',    'Received Bytes [Bytes/sec]'
    'Parris_sent_bytes',        'Schultz_sent_bytes',        'Sent Bytes [Bytes/sec]'
};

%% Load datasets
T220  = load_csv(csv220);
T1100 = load_csv(csv1100);

%% Plot
for i = 1:size(metricDefs, 1)
    pCol      = metricDefs{i, 1};
    sCol      = metricDefs{i, 2};
    ylabelStr = metricDefs{i, 3};

    figure('Name', ylabelStr, 'NumberTitle', 'off', ...
           'Position', [100, 100, 1100, 420]);

    subplot(1, 2, 1);
    plot_metric(T220,  pCol, sCol, ylabelStr, C_PARRIS, C_SCHULTZ, '220 Tags');

    subplot(1, 2, 2);
    plot_metric(T1100, pCol, sCol, ylabelStr, C_PARRIS, C_SCHULTZ, '1100 Tags');
end

fprintf('All %d figures generated.\n', size(metricDefs,1));

%% -------------------------------------------------------------------------
function T = load_csv(filepath)
    T = readtable(filepath, 'PreserveVariableNames', true);
    if ~isdatetime(T.Time)
        try
            T.Time = datetime(T.Time, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
        catch
            T.Time = datetime(T.Time, 'ConvertFrom', 'excel');
        end
    end
end

function plot_metric(T, pCol, sCol, ylabelStr, C_P, C_S, titleStr)
    parris  = T{:, pCol};
    schultz = T{:, sCol};

    parris(isnan(parris))   = 0;
    schultz(isnan(schultz)) = 0;

    t_plot       = [T.Time(1);  T.Time;  T.Time(end)];
    parris_plot  = [0;          parris;  0           ];
    schultz_plot = [0;          schultz; 0           ];

    plot(t_plot, schultz_plot, 'Color', C_S, 'LineWidth', 1.6);
    hold on;
    plot(t_plot, parris_plot,  'Color', C_P, 'LineWidth', 1.6);

    grid on;
    grid minor;
    ax = gca;
    ax.GridAlpha      = 0.30;
    ax.MinorGridAlpha = 0.15;
    ax.XLim = [T.Time(1) - minutes(3), T.Time(end) + minutes(3)];
    ax.XAxis.TickLabelFormat = 'HH:mm';
    xtickformat(ax, 'HH:mm');
    xticks(ax, T.Time(1) : minutes(30) : T.Time(end));

    xlabel('Time');
    ylabel(ylabelStr);
    title(titleStr);

    ymax = max(max(parris_plot), max(schultz_plot));
    if ymax > 0; ylim([0, ymax * 1.1]); else; ylim([0, 1]); end

    lgd = legend({'Schultz Method', 'Parris Method'}, ...
        'Location', 'southoutside', 'Orientation', 'horizontal', 'Box', 'on');
    lgd.FontSize = 9;
    hold off;
end
