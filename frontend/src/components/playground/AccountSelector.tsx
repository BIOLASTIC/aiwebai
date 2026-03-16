import React from 'react';

interface Account {
  id: number;
  label: string;
  health_status: string;
}

interface AccountSelectorProps {
  accounts: Account[];
  selectedAccountId: string;
  onSelect: (accountId: string) => void;
}

const AccountSelector: React.FC<AccountSelectorProps> = ({ 
  accounts, 
  selectedAccountId, 
  onSelect 
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
        {accounts.map(account => (
          <option key={account.id} value={String(account.id)}>
            {account.label} {account.health_status === 'healthy' ? '✓' : '?'}
          </option>
        ))}
      </select>
    </label>
  );
};

export default AccountSelector;