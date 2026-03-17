import React from 'react';

interface AccountCapabilities {
  chat?: boolean;
  image?: boolean;
  video?: boolean;
  music?: boolean;
  research?: boolean;
}

interface Account {
  id: number;
  label: string;
  health_status: string;
  provider?: string;
  capabilities?: AccountCapabilities;
}

interface AccountSelectorProps {
  accounts: Account[];
  selectedAccountId: string;
  onSelect: (accountId: string) => void;
}

const CAPABILITY_ICONS: { key: keyof AccountCapabilities; icon: string }[] = [
  { key: 'chat',     icon: '💬' },
  { key: 'image',    icon: '🖼️' },
  { key: 'video',    icon: '🎬' },
  { key: 'music',    icon: '🎵' },
  { key: 'research', icon: '🔬' },
];

const AccountSelector: React.FC<AccountSelectorProps> = ({
  accounts,
  selectedAccountId,
  onSelect,
}) => {
  return (
    <label className="flex items-center gap-1.5 text-xs text-gray-500">
      <span className="font-medium">Account:</span>
      <select
        value={selectedAccountId}
        onChange={(e) => onSelect(e.target.value)}
        className="bg-gray-100 dark:bg-gray-800 border-0 rounded-lg px-2 py-1.5 text-xs outline-none"
      >
        <option value="auto">Auto</option>
        {accounts.map((account) => {
          const provider = account.provider ?? 'webapi';
          const caps = account.capabilities ?? {};
          const capIcons = CAPABILITY_ICONS
            .filter(({ key }) => caps[key])
            .map(({ icon }) => icon)
            .join(' ');
          const healthMark = account.health_status === 'healthy' ? '✓' : '?';
          const providerTag = provider === 'mcpcli' ? '[mcpcli]' : '[webapi]';
          const label = `${account.label} ${providerTag} ${capIcons} ${healthMark}`.trim();
          return (
            <option key={account.id} value={String(account.id)}>
              {label}
            </option>
          );
        })}
      </select>
    </label>
  );
};

export default AccountSelector;
